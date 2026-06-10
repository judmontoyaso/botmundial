"""Statistical analysis service — Poisson + ELO + xG + Form + H2H + Absences."""

from __future__ import annotations

import logging
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from app.models.match import Match
from app.models.team import GroupStanding, Team
from app.services import data_service

logger = logging.getLogger("app.services.analysis")

# ---------------------------------------------------------------------------
# League-wide constants
# ---------------------------------------------------------------------------
_MEAN_XG_FOR = 1.30
_MEAN_XG_AGAINST = 1.10
_MEAN_GOALS = 1.20
_HOME_FACTOR = 1.04   # calibrated from Qatar 2022 backtest (was 1.08)
_ELO_SCALE = 3000
_DC_RHO = -0.10
_DRAW_BOOST = 1.35    # boosts equal-score probabilities to fix draw underprediction

# ---------------------------------------------------------------------------
# Klement-inspired structural factors: GDP per capita + Population
# Max effect: ±5% for GDP, ±3% for population on team lambda
# ---------------------------------------------------------------------------
_GDP_REF = 15_000       # USD reference (median WC team)
_GDP_MAX = 0.025        # max ±2.5% effect on lambda
_POP_REF_M = 40.0       # millions reference
_POP_MAX = 0.015        # max ±1.5% effect on lambda

_GDP_PER_CAPITA: dict[str, int] = {
    # CONCACAF
    "USA": 85000, "CAN": 55000, "MEX": 11000, "CRC": 14000,
    "PAN": 16000, "HON": 3000,  "JAM": 5800,  "HAI": 1700,
    "CUW": 20000, "TRI": 17000, "SLV": 5000,  "GUA": 5500,
    # CONMEBOL
    "BRA": 10000, "ARG": 13000, "COL": 7000,  "URU": 17000,
    "ECU": 7000,  "CHI": 16000, "BOL": 3500,  "PAR": 5500,
    "PER": 7000,  "VEN": 8000,
    # UEFA
    "FRA": 46000, "ENG": 48000, "ESP": 33000, "GER": 54000,
    "POR": 25000, "NED": 57000, "BEL": 51000, "ITA": 37000,
    "CRO": 20000, "SUI": 92000, "AUT": 57000, "TUR": 12000,
    "SCO": 48000, "ALB": 7000,  "SRB": 10000, "SVN": 30000,
    "HUN": 22000, "ROU": 16000, "SVK": 23000, "UKR": 5000,
    "CZE": 28000, "BIH": 8000,  "GRE": 22000, "NOR": 108000,
    "SWE": 57000, "DEN": 67000, "POL": 20000,
    # AFC
    "JPN": 35000, "KOR": 35000, "AUS": 65000, "IRN": 6000,
    "KSA": 29000, "JOR": 5000,  "QAT": 85000, "IRQ": 7000,
    "UZB": 3000,
    # CAF
    "MAR": 4000,  "EGY": 4300,  "NGA": 2100,  "CMR": 1600,
    "SEN": 2000,  "CIV": 2300,  "GHA": 2200,  "TUN": 3800,
    "ALG": 4200,  "RSA": 7000,  "DRC": 600,   "MLI": 900,
    "CPV": 4000,  "SDN": 800,
    # OFC
    "NZL": 47000,
}

_POPULATION_M: dict[str, float] = {
    # CONCACAF
    "USA": 340,  "CAN": 38,   "MEX": 130,  "CRC": 5,
    "PAN": 4,    "HON": 10,   "JAM": 3,    "HAI": 12,
    "CUW": 0.16, "TRI": 1.4,  "SLV": 6.5,  "GUA": 17,
    # CONMEBOL
    "BRA": 215,  "ARG": 46,   "COL": 52,   "URU": 3.5,
    "ECU": 18,   "CHI": 19,   "BOL": 12,   "PAR": 7,
    "PER": 33,   "VEN": 32,
    # UEFA
    "FRA": 68,   "ENG": 57,   "ESP": 47,   "GER": 83,
    "POR": 10,   "NED": 17,   "BEL": 11,   "ITA": 60,
    "CRO": 4,    "SUI": 8,    "AUT": 9,    "TUR": 85,
    "SCO": 5.5,  "ALB": 2.8,  "SRB": 7,    "SVN": 2,
    "HUN": 10,   "ROU": 19,   "SVK": 5.5,  "UKR": 38,
    "CZE": 10.5, "BIH": 3.3,  "GRE": 10.4, "NOR": 5.5,
    "SWE": 10.5, "DEN": 6,    "POL": 38,
    # AFC
    "JPN": 124,  "KOR": 52,   "AUS": 26,   "IRN": 87,
    "KSA": 36,   "JOR": 10,   "QAT": 3,    "IRQ": 42,
    "UZB": 36,
    # CAF
    "MAR": 37,   "EGY": 105,  "NGA": 220,  "CMR": 28,
    "SEN": 17,   "CIV": 27,   "GHA": 32,   "TUN": 12,
    "ALG": 46,   "RSA": 62,   "DRC": 100,  "MLI": 22,
    "CPV": 0.56, "SDN": 46,
    # OFC
    "NZL": 5,
}


def _gdp_modifier(code: str) -> float:
    """±5% lambda modifier based on GDP per capita (log-scaled, Klement-inspired)."""
    gdp = _GDP_PER_CAPITA.get(code.upper(), _GDP_REF)
    raw = math.log(gdp / _GDP_REF)
    scale = _GDP_MAX / math.log(108_000 / _GDP_REF)  # normalised to Norway (highest)
    return max(-_GDP_MAX, min(_GDP_MAX, raw * scale))


def _pop_modifier(code: str) -> float:
    """±3% lambda modifier based on talent-pool size (log-scaled)."""
    pop = _POPULATION_M.get(code.upper(), _POP_REF_M)
    raw = math.log(max(pop, 0.1) / _POP_REF_M)
    scale = _POP_MAX / math.log(340 / _POP_REF_M)   # normalised to USA (largest WC team)
    return max(-_POP_MAX, min(_POP_MAX, raw * scale))

# ---------------------------------------------------------------------------
# Poisson helpers
# ---------------------------------------------------------------------------

def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0 or k < 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _poisson_sample(lam: float) -> int:
    """Sample from Poisson distribution (Knuth's algorithm). No dependencies."""
    if lam <= 0:
        return 0
    lam = min(lam, 30.0)
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p <= L:
            return k - 1


def build_scoreline_matrix(lam_home: float, lam_away: float, max_goals: int = 5) -> list[list[float]]:
    """
    Returns a (max_goals+1)×(max_goals+1) matrix P(home=h, away=a).
    Applies Dixon-Coles correction for low-scoring results and a draw boost
    factor on all equal-score cells to correct Poisson draw underprediction.
    """
    n = max_goals + 1
    matrix: list[list[float]] = [
        [_poisson_pmf(h, lam_home) * _poisson_pmf(a, lam_away) for a in range(n)]
        for h in range(n)
    ]
    # Dixon-Coles low-score correction
    rho = _DC_RHO
    matrix[0][0] *= max(0.0, 1 - lam_home * lam_away * rho)
    matrix[1][0] *= max(0.0, 1 + lam_away * rho)
    matrix[0][1] *= max(0.0, 1 + lam_home * rho)
    matrix[1][1] *= max(0.0, 1 - rho)
    # Draw boost: multiply all equal-score cells to correct underprediction
    for g in range(n):
        matrix[g][g] *= _DRAW_BOOST
    total = sum(matrix[h][a] for h in range(n) for a in range(n))
    if total > 0:
        matrix = [[round(matrix[h][a] / total, 6) for a in range(n)] for h in range(n)]
    return matrix


def derive_outcome_probs(matrix: list[list[float]]) -> tuple[float, float, float]:
    n = len(matrix)
    home_win = sum(matrix[h][a] for h in range(n) for a in range(n) if h > a)
    draw = sum(matrix[h][h] for h in range(n))
    away_win = sum(matrix[h][a] for h in range(n) for a in range(n) if a > h)
    total = home_win + draw + away_win
    if total > 0:
        home_win /= total; draw /= total; away_win /= total
    return round(home_win, 4), round(draw, 4), round(away_win, 4)


def most_likely_score(matrix: list[list[float]]) -> tuple[int, int]:
    n = len(matrix)
    best_prob = -1.0
    best_h, best_a = 1, 1
    for h in range(n):
        for a in range(n):
            if matrix[h][a] > best_prob:
                best_prob = matrix[h][a]
                best_h, best_a = h, a
    return best_h, best_a


def predicted_outcome(hw: float, dw: float, aw: float) -> str:
    """Most probable outcome label given the three outcome probabilities."""
    if hw >= dw and hw >= aw:
        return "home"
    if aw >= hw and aw >= dw:
        return "away"
    return "draw"


def most_likely_score_for_outcome(
    matrix: list[list[float]], outcome: str
) -> tuple[int, int]:
    """
    Most probable scoreline CONSISTENT with the given outcome, so the
    predicted score never contradicts the outcome probabilities
    (e.g. probabilities favouring the home side but a drawn scoreline).
    """
    n = len(matrix)
    best_p = -1.0
    best = (1, 1) if outcome == "draw" else ((1, 0) if outcome == "home" else (0, 1))
    for h in range(n):
        for a in range(n):
            if outcome == "home" and h <= a:
                continue
            if outcome == "away" and a <= h:
                continue
            if outcome == "draw" and h != a:
                continue
            if matrix[h][a] > best_p:
                best_p = matrix[h][a]
                best = (h, a)
    return best


def outcome_confidence(hw: float, dw: float, aw: float) -> float:
    """
    Confidence tied to the displayed probabilities: probability of the
    predicted outcome plus a bonus for its margin over the runner-up.
    A 60/25/15 match scores higher than a 40/32/28 one.
    """
    top, second, _ = sorted((hw, dw, aw), reverse=True)
    return round(min(0.95, top + 0.30 * (top - second)), 4)

# ---------------------------------------------------------------------------
# Team strength
# ---------------------------------------------------------------------------

def calculate_team_strength(team: Team) -> float:
    elo_score = max(0.0, min(50.0, (team.stats.elo_rating - 1400) / 700 * 50))
    form_10 = (team.stats.wins_last_10 * 3 + team.stats.draws_last_10) / 30
    form_5_bonus = team.stats.form_last_5 / 5
    form_score = 20 * (0.6 * form_10 + 0.4 * form_5_bonus)
    attack = min(team.stats.xg_for_avg / 2.0, 1.0) * 10
    defense = max(0.0, 1.0 - team.stats.xg_against_avg / 2.0) * 10
    xg_score = attack + defense
    exp_score = min(team.stats.world_cup_appearances / 20, 1.0) * 10
    return round(min(max(elo_score + form_score + xg_score + exp_score, 0.0), 100.0), 1)

# ---------------------------------------------------------------------------
# Climate and Location Modifiers
# ---------------------------------------------------------------------------

CITY_CLIMATES = {
    "Mexico City":    {"type": "altitude",  "desc": "Alta Altitud / Cálido",    "temp": 25},
    "Guadalajara":    {"type": "altitude",  "desc": "Altitud Moderada / Cálido","temp": 28},
    "Monterrey":      {"type": "hot_humid", "desc": "Muy Caluroso / Húmedo",    "temp": 34},
    "Miami":          {"type": "hot_humid", "desc": "Caluroso / Muy Húmedo",    "temp": 31},
    "Houston":        {"type": "hot_humid", "desc": "Caluroso / Húmedo",        "temp": 33},
    "Dallas":         {"type": "hot",       "desc": "Muy Caluroso",             "temp": 34},
    "Arlington":      {"type": "hot",       "desc": "Muy Caluroso",             "temp": 34},
    "Atlanta":        {"type": "hot_humid", "desc": "Caluroso / Húmedo",        "temp": 31},
    "Kansas City":    {"type": "warm",      "desc": "Cálido",                   "temp": 29},
    "Philadelphia":   {"type": "warm",      "desc": "Cálido",                   "temp": 27},
    "New York":       {"type": "warm",      "desc": "Cálido",                   "temp": 26},
    "East Rutherford":{"type": "warm",      "desc": "Cálido",                   "temp": 26},
    "Boston":         {"type": "warm",      "desc": "Cálido",                   "temp": 25},
    "Foxborough":     {"type": "warm",      "desc": "Cálido",                   "temp": 25},
    "Los Angeles":    {"type": "warm",      "desc": "Cálido / Seco",            "temp": 26},
    "Santa Clara":    {"type": "warm",      "desc": "Cálido",                   "temp": 25},
    "San Francisco":  {"type": "mild",      "desc": "Templado",                 "temp": 20},
    "Seattle":        {"type": "mild",      "desc": "Templado",                 "temp": 22},
    "Vancouver":      {"type": "mild",      "desc": "Templado",                 "temp": 21},
    "Toronto":        {"type": "mild",      "desc": "Templado",                 "temp": 24},
}


def get_climate_modifier(team: Team, city: str) -> float:
    if city not in CITY_CLIMATES:
        return 0.0
    climate = CITY_CLIMATES[city]["type"]
    confed = team.confederation.upper()
    if climate == "altitude":
        if confed in ("CONMEBOL", "CONCACAF"): return 0.08
        if confed == "UEFA": return -0.10
        return -0.05
    if climate in ("hot_humid", "hot"):
        if confed in ("CAF", "CONMEBOL", "CONCACAF"): return 0.06
        if confed == "UEFA": return -0.08
        return 0.0
    if climate == "mild":
        if confed == "UEFA": return 0.05
        return 0.0
    return 0.0


def get_continent_advantage(team: Team) -> float:
    confed = team.confederation.upper()
    if confed == "CONCACAF": return 0.12
    if confed == "CONMEBOL": return 0.07
    return 0.0

# ---------------------------------------------------------------------------
# ELO quality adjustment
# ---------------------------------------------------------------------------

def elo_lambda_factors(elo_home: int, elo_away: int) -> tuple[float, float]:
    diff = elo_home - elo_away
    factor = diff / _ELO_SCALE
    return round(1.0 + factor, 4), round(1.0 - factor, 4)

# ---------------------------------------------------------------------------
# New: Form / H2H / Absence modifiers
# ---------------------------------------------------------------------------

def _form_modifier(team: Team) -> float:
    """Form recency modifier -0.10…+0.10 based on last-5 wins (0-5)."""
    form = team.stats.form_last_5
    return round((form - 2.5) / 25.0, 4)


def _h2h_modifier(h2h: dict, perspective_code: str) -> float:
    """Historical H2H advantage -0.08…+0.08. Needs ≥3 matches to activate."""
    total = (
        h2h.get("total_matches")
        or h2h.get("h2h_wins_a", 0) + h2h.get("h2h_wins_b", 0) + h2h.get("h2h_draws", 0)
    )
    if total < 3:
        return 0.0
    if perspective_code == h2h.get("team_a_code"):
        wins = h2h.get("h2h_wins_a", 0)
        losses = h2h.get("h2h_wins_b", 0)
    else:
        wins = h2h.get("h2h_wins_b", 0)
        losses = h2h.get("h2h_wins_a", 0)
    return round((wins - losses) / total * 0.08, 4)


def _absence_modifier(absences: list) -> float:
    """Negative lambda modifier for missing players. Max -0.12."""
    if not absences:
        return 0.0
    impact = sum(a.get("importance", 2) * 0.02 for a in absences)
    return round(-min(impact, 0.12), 4)

# ---------------------------------------------------------------------------
# Internal: shared lambda computation used by both predict and simulation
# ---------------------------------------------------------------------------

def _compute_lambdas(
    home: Team,
    away: Team,
    match: Optional[Match] = None,
    all_h2h: Optional[dict] = None,
    all_abs: Optional[dict] = None,
) -> tuple[float, float]:
    """
    Core lambda computation. When all_h2h / all_abs are provided (pre-fetched dicts),
    no additional DB calls are made — used in Monte Carlo for speed.
    """
    ha = home.stats.xg_for_avg / _MEAN_XG_FOR
    hd = home.stats.xg_against_avg / _MEAN_XG_AGAINST
    aa = away.stats.xg_for_avg / _MEAN_XG_FOR
    ad = away.stats.xg_against_avg / _MEAN_XG_AGAINST

    lh = ha * ad * _MEAN_GOALS * _HOME_FACTOR
    la = aa * hd * _MEAN_GOALS

    # Climate + continent
    city = match.city if match else ""
    lh *= (1.0 + get_climate_modifier(home, city) + get_continent_advantage(home))
    la *= (1.0 + get_climate_modifier(away, city) + get_continent_advantage(away))

    # ELO quality adjustment
    ef_h, ef_a = elo_lambda_factors(home.stats.elo_rating, away.stats.elo_rating)
    lh = max(0.3, lh * ef_h)
    la = max(0.3, la * ef_a)

    # Form recency (no DB call)
    lh = max(0.3, lh * (1.0 + _form_modifier(home)))
    la = max(0.3, la * (1.0 + _form_modifier(away)))

    # Structural factors: GDP per capita + population (Klement-inspired).
    # Applied at reduced weight (×0.4) to avoid double-counting with ELO,
    # which already captures historical performance correlated with GDP/population.
    gdp_h = _gdp_modifier(home.code) * 0.4
    gdp_a = _gdp_modifier(away.code) * 0.4
    pop_h = _pop_modifier(home.code) * 0.4
    pop_a = _pop_modifier(away.code) * 0.4
    lh = max(0.3, lh * (1.0 + gdp_h + pop_h))
    la = max(0.3, la * (1.0 + gdp_a + pop_a))

    # H2H historical factor
    h2h_rec = None
    if all_h2h is not None:
        h2h_rec = all_h2h.get((home.code, away.code)) or all_h2h.get((away.code, home.code))
    if h2h_rec:
        lh = max(0.3, lh * (1.0 + _h2h_modifier(h2h_rec, home.code)))
        la = max(0.3, la * (1.0 + _h2h_modifier(h2h_rec, away.code)))

    # Player absence modifier
    if all_abs is not None:
        home_abs = list(all_abs.get(home.code, []))
        away_abs = list(all_abs.get(away.code, []))
        lh = max(0.3, lh * (1.0 + _absence_modifier(home_abs)))
        la = max(0.3, la * (1.0 + _absence_modifier(away_abs)))

    return round(lh, 4), round(la, 4)

# ---------------------------------------------------------------------------
# Main Poisson prediction
# ---------------------------------------------------------------------------

def predict_match_statistical(
    home_team: Team,
    away_team: Team,
    match: Optional[Match] = None,
) -> dict:
    """
    Full Poisson-based prediction with: xG, ELO, climate, continent,
    form recency, H2H history, and player absences.
    """
    # Fetch H2H and absences from DB (gracefully skip if tables don't exist)
    all_h2h: dict = {}
    all_abs: dict = defaultdict(list)
    try:
        for rec in data_service.get_all_h2h():
            all_h2h[(rec["team_a_code"], rec["team_b_code"])] = rec
    except Exception:
        pass
    try:
        for rec in data_service.get_all_active_absences():
            all_abs[rec["team_code"]].append(rec)
    except Exception:
        pass

    lh, la = _compute_lambdas(home_team, away_team, match, all_h2h, all_abs)

    # Also track intermediate values for debug/display
    city = match.city if match else ""
    climate_desc = CITY_CLIMATES.get(city, {}).get("desc", "")
    home_climate_mod = get_climate_modifier(home_team, city)
    away_climate_mod = get_climate_modifier(away_team, city)
    home_cont_mod = get_continent_advantage(home_team)
    away_cont_mod = get_continent_advantage(away_team)

    h2h_rec = all_h2h.get((home_team.code, away_team.code)) or all_h2h.get((away_team.code, home_team.code))
    home_h2h_mod = _h2h_modifier(h2h_rec, home_team.code) if h2h_rec else 0.0
    away_h2h_mod = _h2h_modifier(h2h_rec, away_team.code) if h2h_rec else 0.0

    home_abs_mod = _absence_modifier(list(all_abs.get(home_team.code, [])))
    away_abs_mod = _absence_modifier(list(all_abs.get(away_team.code, [])))

    matrix = build_scoreline_matrix(lh, la)
    home_win_prob, draw_prob, away_win_prob = derive_outcome_probs(matrix)
    # Score and confidence derived from the same matrix/probabilities so
    # every number shown is mutually consistent.
    outcome = predicted_outcome(home_win_prob, draw_prob, away_win_prob)
    pred_home, pred_away = most_likely_score_for_outcome(matrix, outcome)
    confidence = outcome_confidence(home_win_prob, draw_prob, away_win_prob)

    return {
        "predicted_home_score": pred_home,
        "predicted_away_score": pred_away,
        "home_win_prob": home_win_prob,
        "draw_prob": draw_prob,
        "away_win_prob": away_win_prob,
        "confidence": confidence,
        "poisson_home_lambda": lh,
        "poisson_away_lambda": la,
        "scoreline_matrix": matrix,
        "home_strength": calculate_team_strength(home_team),
        "away_strength": calculate_team_strength(away_team),
        "home_elo": home_team.stats.elo_rating,
        "away_elo": away_team.stats.elo_rating,
        "home_xg_for": home_team.stats.xg_for_avg,
        "away_xg_for": away_team.stats.xg_for_avg,
        "home_xg_against": home_team.stats.xg_against_avg,
        "away_xg_against": away_team.stats.xg_against_avg,
        "home_form_mod": _form_modifier(home_team),
        "away_form_mod": _form_modifier(away_team),
        "home_h2h_mod": home_h2h_mod,
        "away_h2h_mod": away_h2h_mod,
        "home_absence_mod": home_abs_mod,
        "away_absence_mod": away_abs_mod,
        "home_climate_mod": home_climate_mod,
        "away_climate_mod": away_climate_mod,
        "home_cont_mod": home_cont_mod,
        "away_cont_mod": away_cont_mod,
        "home_gdp_mod": round(_gdp_modifier(home_team.code), 4),
        "away_gdp_mod": round(_gdp_modifier(away_team.code), 4),
        "home_pop_mod": round(_pop_modifier(home_team.code), 4),
        "away_pop_mod": round(_pop_modifier(away_team.code), 4),
        "home_gdp": _GDP_PER_CAPITA.get(home_team.code.upper(), _GDP_REF),
        "away_gdp": _GDP_PER_CAPITA.get(away_team.code.upper(), _GDP_REF),
        "home_pop_m": _POPULATION_M.get(home_team.code.upper(), _POP_REF_M),
        "away_pop_m": _POPULATION_M.get(away_team.code.upper(), _POP_REF_M),
        "city": city,
        "climate_desc": climate_desc,
    }

# ---------------------------------------------------------------------------
# Head-to-head comparison
# ---------------------------------------------------------------------------

def compare_teams(team_a: Team, team_b: Team) -> dict:
    str_a = calculate_team_strength(team_a)
    str_b = calculate_team_strength(team_b)
    total = str_a + str_b if (str_a + str_b) > 0 else 1
    return {
        "team_a": {
            "code": team_a.code, "name": team_a.name,
            "strength": str_a, "fifa_ranking": team_a.fifa_ranking,
            "elo_rating": team_a.stats.elo_rating,
            "form": f"{team_a.stats.wins_last_10}W-{team_a.stats.draws_last_10}D-{team_a.stats.losses_last_10}L",
            "form_last_5": team_a.stats.form_last_5,
            "xg_for": team_a.stats.xg_for_avg, "xg_against": team_a.stats.xg_against_avg,
            "clean_sheets": team_a.stats.clean_sheets_last_10,
        },
        "team_b": {
            "code": team_b.code, "name": team_b.name,
            "strength": str_b, "fifa_ranking": team_b.fifa_ranking,
            "elo_rating": team_b.stats.elo_rating,
            "form": f"{team_b.stats.wins_last_10}W-{team_b.stats.draws_last_10}D-{team_b.stats.losses_last_10}L",
            "form_last_5": team_b.stats.form_last_5,
            "xg_for": team_b.stats.xg_for_avg, "xg_against": team_b.stats.xg_against_avg,
            "clean_sheets": team_b.stats.clean_sheets_last_10,
        },
        "advantage": team_a.code if str_a >= str_b else team_b.code,
        "strength_diff": round(abs(str_a - str_b), 1),
        "a_win_pct": round(str_a / total * 100, 1),
        "b_win_pct": round(str_b / total * 100, 1),
    }

# ---------------------------------------------------------------------------
# Group standings simulation
# ---------------------------------------------------------------------------

def calculate_group_standings(group_letter: str) -> list[GroupStanding]:
    teams = data_service.get_teams_by_group(group_letter.upper())
    if not teams:
        return []
    matches = data_service.load_matches(stage="group", group=group_letter.upper())
    # Prefer cached AI predictions so standings match the predictions page
    try:
        ai_preds = data_service.get_all_ai_predictions()
    except Exception:
        ai_preds = {}
    standings: dict[str, GroupStanding] = {
        t.code: GroupStanding(team_code=t.code, team_name=t.name) for t in teams
    }
    for match in matches:
        home = data_service.get_team_by_code(match.home_team_code)
        away = data_service.get_team_by_code(match.away_team_code)
        if not home or not away:
            continue
        if match.home_score is not None and match.away_score is not None:
            h_goals, a_goals = match.home_score, match.away_score
        elif (ai := ai_preds.get(match.id)) is not None:
            h_goals, a_goals = ai.predicted_home_score, ai.predicted_away_score
        else:
            pred = predict_match_statistical(home, away, match)
            h_goals = pred["predicted_home_score"]
            a_goals = pred["predicted_away_score"]
        h = standings[home.code]
        a = standings[away.code]
        h.played += 1; a.played += 1
        h.goals_for += h_goals; h.goals_against += a_goals
        a.goals_for += a_goals; a.goals_against += h_goals
        h.goal_difference = h.goals_for - h.goals_against
        a.goal_difference = a.goals_for - a.goals_against
        if h_goals > a_goals:
            h.won += 1; h.points += 3; a.lost += 1
        elif h_goals < a_goals:
            a.won += 1; a.points += 3; h.lost += 1
        else:
            h.drawn += 1; a.drawn += 1; h.points += 1; a.points += 1
    sorted_standings = sorted(
        standings.values(),
        key=lambda s: (s.points, s.goal_difference, s.goals_for),
        reverse=True,
    )
    for idx, s in enumerate(sorted_standings, 1):
        s.position = idx
    return sorted_standings

# ---------------------------------------------------------------------------
# Monte Carlo tournament simulation
# ---------------------------------------------------------------------------

def run_tournament_simulation(n_simulations: int = 5000) -> dict:
    """
    Monte Carlo simulation of World Cup 2026.
    Returns P(champion), P(finalist), P(top4), P(top8), P(group_advance) per team.
    Pre-computes Poisson lambdas (2 bulk DB calls) then runs pure-Python simulation.
    """
    all_teams = {t.code: t for t in data_service.load_teams()}
    group_matches = data_service.load_matches(stage="group")

    # Build group structure
    groups: dict[str, list[str]] = {}
    group_triples: list[tuple[str, str, str, object]] = []
    for m in group_matches:
        g = m.group_letter
        if g not in groups:
            groups[g] = []
        if m.home_team_code not in groups[g]:
            groups[g].append(m.home_team_code)
        if m.away_team_code not in groups[g]:
            groups[g].append(m.away_team_code)
        group_triples.append((g, m.home_team_code, m.away_team_code, m))

    # Pre-fetch H2H and absences in bulk (2 DB calls)
    all_h2h: dict = {}
    all_abs: dict = defaultdict(list)
    try:
        for rec in data_service.get_all_h2h():
            all_h2h[(rec["team_a_code"], rec["team_b_code"])] = rec
    except Exception:
        pass
    try:
        for rec in data_service.get_all_active_absences():
            all_abs[rec["team_code"]].append(rec)
    except Exception:
        pass

    # Pre-compute lambdas for all group matchups
    lam_cache: dict[tuple[str, str], tuple[float, float]] = {}
    for _, hc, ac, match in group_triples:
        key = (hc, ac)
        if key in lam_cache:
            continue
        if match.home_score is not None:
            continue  # actual result, no lambda needed
        home = all_teams.get(hc)
        away = all_teams.get(ac)
        lam_cache[key] = _compute_lambdas(home, away, match, all_h2h, all_abs) if (home and away) else (1.2, 1.0)

    def get_lams(hc: str, ac: str) -> tuple[float, float]:
        key = (hc, ac)
        if key not in lam_cache:
            rev = (ac, hc)
            if rev in lam_cache:
                la, lh = lam_cache[rev]
                lam_cache[key] = (lh, la)
            else:
                home = all_teams.get(hc)
                away = all_teams.get(ac)
                lam_cache[key] = _compute_lambdas(home, away, None, all_h2h, all_abs) if (home and away) else (1.2, 1.0)
        return lam_cache[key]

    def sim_goals(hc: str, ac: str, match=None) -> tuple[int, int]:
        if match and getattr(match, "home_score", None) is not None:
            return match.home_score, match.away_score
        lh, la = get_lams(hc, ac)
        return _poisson_sample(lh), _poisson_sample(la)

    def sim_knockout(hc: str, ac: str) -> str:
        lh, la = get_lams(hc, ac)
        h, a = _poisson_sample(lh), _poisson_sample(la)
        if h != a:
            return hc if h > a else ac
        # Penalty shootout — ELO-biased coin flip
        elo_h = all_teams[hc].stats.elo_rating if hc in all_teams else 1700
        elo_a = all_teams[ac].stats.elo_rating if ac in all_teams else 1700
        p = 0.5 + (elo_h - elo_a) / 6000.0
        return hc if random.random() < p else ac

    champion_c: dict[str, int] = defaultdict(int)
    finalist_c: dict[str, int] = defaultdict(int)
    top4_c: dict[str, int] = defaultdict(int)
    top8_c: dict[str, int] = defaultdict(int)
    advance_c: dict[str, int] = defaultdict(int)

    sorted_groups = sorted(groups.keys())

    for _ in range(n_simulations):
        pts: dict[str, int] = defaultdict(int)
        gf: dict[str, int] = defaultdict(int)
        ga: dict[str, int] = defaultdict(int)

        for _, hc, ac, match in group_triples:
            h, a = sim_goals(hc, ac, match)
            gf[hc] += h; ga[hc] += a
            gf[ac] += a; ga[ac] += h
            if h > a:   pts[hc] += 3
            elif a > h: pts[ac] += 3
            else:       pts[hc] += 1; pts[ac] += 1

        qualifiers: list[str] = []
        thirds: list[tuple[int, int, int, str]] = []

        for g in sorted_groups:
            ranked = sorted(
                groups[g],
                key=lambda c: (pts[c], gf[c] - ga[c], gf[c]),
                reverse=True,
            )
            qualifiers.append(ranked[0])
            qualifiers.append(ranked[1])
            advance_c[ranked[0]] += 1
            advance_c[ranked[1]] += 1
            if len(ranked) >= 3:
                t = ranked[2]
                thirds.append((pts[t], gf[t] - ga[t], gf[t], t))

        thirds.sort(reverse=True)
        for _, _, _, t in thirds[:8]:
            qualifiers.append(t)
            advance_c[t] += 1

        # Knockout: R32 (32→16) → R16 (16→8 = top8) → QF (8→4 = top4) → SF (4→2 = finalists) → Final
        r32_w = [sim_knockout(qualifiers[i], qualifiers[i + 1]) for i in range(0, 32, 2)]
        r16_w = [sim_knockout(r32_w[i], r32_w[i + 1]) for i in range(0, 16, 2)]
        qf_w  = [sim_knockout(r16_w[i], r16_w[i + 1]) for i in range(0, 8, 2)]
        sf_w  = [sim_knockout(qf_w[i],  qf_w[i + 1])  for i in range(0, 4, 2)]
        winner = sim_knockout(sf_w[0], sf_w[1])

        for c in r16_w: top8_c[c] += 1
        for c in qf_w:  top4_c[c] += 1
        for c in sf_w:  finalist_c[c] += 1
        champion_c[winner] += 1

    results = [
        {
            "team_code": code,
            "team_name": t.name,
            "flag_emoji": t.flag_emoji,
            "elo": t.stats.elo_rating,
            "confederation": t.confederation,
            "p_champion":     round(champion_c.get(code, 0)  / n_simulations * 100, 1),
            "p_finalist":     round(finalist_c.get(code, 0)  / n_simulations * 100, 1),
            "p_top4":         round(top4_c.get(code, 0)      / n_simulations * 100, 1),
            "p_top8":         round(top8_c.get(code, 0)      / n_simulations * 100, 1),
            "p_group_advance": round(advance_c.get(code, 0)  / n_simulations * 100, 1),
        }
        for code, t in all_teams.items()
    ]
    results.sort(key=lambda x: x["p_champion"], reverse=True)

    return {
        "simulations": n_simulations,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "teams": results,
    }
