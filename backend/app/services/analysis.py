"""Statistical analysis service — Poisson + ELO + xG model."""

from __future__ import annotations

import math
from typing import Optional

from app.models.match import Match
from app.models.team import GroupStanding, Team
from app.services import data_service

# ---------------------------------------------------------------------------
# League-wide constants (international football averages)
# ---------------------------------------------------------------------------
_MEAN_XG_FOR = 1.30       # average xG scored per team per match
_MEAN_XG_AGAINST = 1.10   # average xG conceded per team per match
_MEAN_GOALS = 1.20        # average goals per team per match (slightly below xG)
_HOME_FACTOR = 1.08       # mild home advantage (WC neutral-country context)
_ELO_SCALE = 3000         # dampening: 500 ELO gap → +/-17% lambda change
_DC_RHO = -0.10           # Dixon-Coles low-score correlation parameter

# ---------------------------------------------------------------------------
# Poisson helpers
# ---------------------------------------------------------------------------

def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0 or k < 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def build_scoreline_matrix(lam_home: float, lam_away: float, max_goals: int = 5) -> list[list[float]]:
    """
    Returns a (max_goals+1) × (max_goals+1) matrix where
    matrix[h][a] = P(home scores h, away scores a).
    Applies Dixon-Coles correction for scorelines with h+a ≤ 1.
    """
    n = max_goals + 1
    matrix: list[list[float]] = [
        [_poisson_pmf(h, lam_home) * _poisson_pmf(a, lam_away) for a in range(n)]
        for h in range(n)
    ]
    # Dixon-Coles correction for low-scoring draws/results
    rho = _DC_RHO
    matrix[0][0] *= max(0.0, 1 - lam_home * lam_away * rho)
    matrix[1][0] *= max(0.0, 1 + lam_away * rho)
    matrix[0][1] *= max(0.0, 1 + lam_home * rho)
    matrix[1][1] *= max(0.0, 1 - rho)
    # Normalise so probabilities sum to ~1
    total = sum(matrix[h][a] for h in range(n) for a in range(n))
    if total > 0:
        matrix = [[round(matrix[h][a] / total, 6) for a in range(n)] for h in range(n)]
    return matrix


def derive_outcome_probs(matrix: list[list[float]]) -> tuple[float, float, float]:
    """Derive home_win / draw / away_win from a scoreline matrix."""
    n = len(matrix)
    home_win = sum(matrix[h][a] for h in range(n) for a in range(n) if h > a)
    draw = sum(matrix[h][h] for h in range(n))
    away_win = sum(matrix[h][a] for h in range(n) for a in range(n) if a > h)
    total = home_win + draw + away_win
    if total > 0:
        home_win /= total
        draw /= total
        away_win /= total
    return round(home_win, 4), round(draw, 4), round(away_win, 4)


def most_likely_score(matrix: list[list[float]]) -> tuple[int, int]:
    """Return the (home, away) scoreline with the highest probability."""
    n = len(matrix)
    best_prob = -1.0
    best_h, best_a = 1, 1
    for h in range(n):
        for a in range(n):
            if matrix[h][a] > best_prob:
                best_prob = matrix[h][a]
                best_h, best_a = h, a
    return best_h, best_a

# ---------------------------------------------------------------------------
# Team strength helpers
# ---------------------------------------------------------------------------

def calculate_team_strength(team: Team) -> float:
    """
    Composite strength score 0-100 using ELO (primary), form, xG and WC experience.
    Used for display / comparison — the Poisson model uses xG directly.
    """
    # ELO component (50 pts max) — normalised between ~1400 (weakest) and ~2100 (strongest)
    elo_score = max(0.0, min(50.0, (team.stats.elo_rating - 1400) / 700 * 50))

    # Form component (25 pts max) — last-10 weighted + last-5 recency bonus
    form_10 = (team.stats.wins_last_10 * 3 + team.stats.draws_last_10) / 30  # 0-1
    form_5_bonus = team.stats.form_last_5 / 5  # 0-1
    form_score = 20 * (0.6 * form_10 + 0.4 * form_5_bonus)  # max 20

    # xG component (20 pts max)
    attack = min(team.stats.xg_for_avg / 2.0, 1.0) * 10
    defense = max(0.0, 1.0 - team.stats.xg_against_avg / 2.0) * 10
    xg_score = attack + defense

    # Experience component (10 pts max)
    exp_score = min(team.stats.world_cup_appearances / 20, 1.0) * 10

    return round(min(max(elo_score + form_score + xg_score + exp_score, 0.0), 100.0), 1)

# ---------------------------------------------------------------------------
# Climate and Location Modifiers
# ---------------------------------------------------------------------------

CITY_CLIMATES = {
    "Mexico City":   {"type": "altitude",  "desc": "Alta Altitud / Cálido",      "temp": 25},
    "Guadalajara":   {"type": "altitude",  "desc": "Altitud Moderada / Cálido",  "temp": 28},
    "Monterrey":     {"type": "hot_humid", "desc": "Muy Caluroso / Húmedo",      "temp": 34},
    "Miami":         {"type": "hot_humid", "desc": "Caluroso / Muy Húmedo",      "temp": 31},
    "Houston":       {"type": "hot_humid", "desc": "Caluroso / Húmedo",          "temp": 33},
    "Dallas":        {"type": "hot",       "desc": "Muy Caluroso",               "temp": 34},
    "Arlington":     {"type": "hot",       "desc": "Muy Caluroso",               "temp": 34},
    "Atlanta":       {"type": "hot_humid", "desc": "Caluroso / Húmedo",          "temp": 31},
    "Kansas City":   {"type": "warm",      "desc": "Cálido",                     "temp": 29},
    "Philadelphia":  {"type": "warm",      "desc": "Cálido",                     "temp": 27},
    "New York":      {"type": "warm",      "desc": "Cálido",                     "temp": 26},
    "East Rutherford": {"type": "warm",    "desc": "Cálido",                     "temp": 26},
    "Boston":        {"type": "warm",      "desc": "Cálido",                     "temp": 25},
    "Foxborough":    {"type": "warm",      "desc": "Cálido",                     "temp": 25},
    "Los Angeles":   {"type": "warm",      "desc": "Cálido / Seco",              "temp": 26},
    "Santa Clara":   {"type": "warm",      "desc": "Cálido",                     "temp": 25},
    "San Francisco": {"type": "mild",      "desc": "Templado",                   "temp": 20},
    "Seattle":       {"type": "mild",      "desc": "Templado",                   "temp": 22},
    "Vancouver":     {"type": "mild",      "desc": "Templado",                   "temp": 21},
    "Toronto":       {"type": "mild",      "desc": "Templado",                   "temp": 24},
}


def get_climate_modifier(team: Team, city: str) -> float:
    """Return a goal-rate modifier (-0.12 to +0.12) based on team adaptation."""
    if city not in CITY_CLIMATES:
        return 0.0
    climate = CITY_CLIMATES[city]["type"]
    confed = team.confederation.upper()
    if climate == "altitude":
        if confed in ("CONMEBOL", "CONCACAF"):
            return 0.08
        if confed == "UEFA":
            return -0.10
        return -0.05
    if climate in ("hot_humid", "hot"):
        if confed in ("CAF", "CONMEBOL", "CONCACAF"):
            return 0.06
        if confed == "UEFA":
            return -0.08
        return 0.0
    if climate == "mild":
        if confed == "UEFA":
            return 0.05
        return 0.0
    return 0.0


def get_continent_advantage(team: Team) -> float:
    """Continent-home advantage modifier for North America 2026."""
    confed = team.confederation.upper()
    if confed == "CONCACAF":
        return 0.12
    if confed == "CONMEBOL":
        return 0.07
    return 0.0

# ---------------------------------------------------------------------------
# ELO-based quality adjustment
# ---------------------------------------------------------------------------

def elo_lambda_factors(elo_home: int, elo_away: int) -> tuple[float, float]:
    """
    Returns (home_factor, away_factor) based on ELO gap.
    Keeps adjustments mild: ±500 ELO → ±10% lambda change.
    """
    diff = elo_home - elo_away
    factor = diff / _ELO_SCALE
    return round(1.0 + factor, 4), round(1.0 - factor, 4)

# ---------------------------------------------------------------------------
# Main Poisson prediction
# ---------------------------------------------------------------------------

def predict_match_statistical(home_team: Team, away_team: Team, match: Optional[Match] = None) -> dict:
    """
    Generate a Poisson-based statistical prediction.
    Uses xG data for attack/defense ratings, ELO for quality adjustment,
    and climate/continent modifiers.
    """
    # Base attack/defense ratings relative to league average
    home_attack = home_team.stats.xg_for_avg / _MEAN_XG_FOR
    home_defense = home_team.stats.xg_against_avg / _MEAN_XG_AGAINST
    away_attack = away_team.stats.xg_for_avg / _MEAN_XG_FOR
    away_defense = away_team.stats.xg_against_avg / _MEAN_XG_AGAINST

    # Raw Poisson lambdas (Dixon-Coles formulation)
    lambda_home = home_attack * away_defense * _MEAN_GOALS * _HOME_FACTOR
    lambda_away = away_attack * home_defense * _MEAN_GOALS

    # Climate and continent adjustments
    city = ""
    climate_desc = ""
    home_climate_mod = 0.0
    away_climate_mod = 0.0
    home_cont_mod = get_continent_advantage(home_team)
    away_cont_mod = get_continent_advantage(away_team)

    if match and match.city:
        city = match.city
        home_climate_mod = get_climate_modifier(home_team, city)
        away_climate_mod = get_climate_modifier(away_team, city)
        if city in CITY_CLIMATES:
            climate_desc = CITY_CLIMATES[city]["desc"]

    lambda_home *= (1.0 + home_climate_mod + home_cont_mod)
    lambda_away *= (1.0 + away_climate_mod + away_cont_mod)

    # ELO quality adjustment (mild)
    elo_h, elo_a = elo_lambda_factors(home_team.stats.elo_rating, away_team.stats.elo_rating)
    lambda_home = max(0.3, round(lambda_home * elo_h, 4))
    lambda_away = max(0.3, round(lambda_away * elo_a, 4))

    # Build scoreline probability matrix
    matrix = build_scoreline_matrix(lambda_home, lambda_away)
    home_win_prob, draw_prob, away_win_prob = derive_outcome_probs(matrix)
    # Use round(λ) — the expected value — instead of the mode.
    # The mode of Poisson is floor(λ), which gives 1-1 for any balanced match
    # where both λ ≈ 1.0–1.74. round(λ) is more varied and intuitive.
    pred_home = max(0, round(lambda_home))
    pred_away = max(0, round(lambda_away))

    # Confidence: mixture of probability gap and ELO certainty
    elo_diff = abs(home_team.stats.elo_rating - away_team.stats.elo_rating)
    prob_gap = abs(home_win_prob - away_win_prob)
    confidence = round(min(0.50 + elo_diff / 2000 + prob_gap * 0.3, 0.95), 3)

    return {
        "predicted_home_score": pred_home,
        "predicted_away_score": pred_away,
        "home_win_prob": home_win_prob,
        "draw_prob": draw_prob,
        "away_win_prob": away_win_prob,
        "confidence": confidence,
        "poisson_home_lambda": lambda_home,
        "poisson_away_lambda": lambda_away,
        "scoreline_matrix": matrix,
        "home_strength": calculate_team_strength(home_team),
        "away_strength": calculate_team_strength(away_team),
        "home_elo": home_team.stats.elo_rating,
        "away_elo": away_team.stats.elo_rating,
        "home_xg_for": home_team.stats.xg_for_avg,
        "away_xg_for": away_team.stats.xg_for_avg,
        "home_xg_against": home_team.stats.xg_against_avg,
        "away_xg_against": away_team.stats.xg_against_avg,
        "home_climate_mod": home_climate_mod,
        "away_climate_mod": away_climate_mod,
        "home_cont_mod": home_cont_mod,
        "away_cont_mod": away_cont_mod,
        "city": city,
        "climate_desc": climate_desc,
    }

# ---------------------------------------------------------------------------
# Head-to-head comparison
# ---------------------------------------------------------------------------

def compare_teams(team_a: Team, team_b: Team) -> dict:
    """Return a comparison dict for two teams."""
    str_a = calculate_team_strength(team_a)
    str_b = calculate_team_strength(team_b)
    total = str_a + str_b if (str_a + str_b) > 0 else 1

    return {
        "team_a": {
            "code": team_a.code,
            "name": team_a.name,
            "strength": str_a,
            "fifa_ranking": team_a.fifa_ranking,
            "elo_rating": team_a.stats.elo_rating,
            "form": f"{team_a.stats.wins_last_10}W-{team_a.stats.draws_last_10}D-{team_a.stats.losses_last_10}L",
            "form_last_5": team_a.stats.form_last_5,
            "xg_for": team_a.stats.xg_for_avg,
            "xg_against": team_a.stats.xg_against_avg,
            "clean_sheets": team_a.stats.clean_sheets_last_10,
        },
        "team_b": {
            "code": team_b.code,
            "name": team_b.name,
            "strength": str_b,
            "fifa_ranking": team_b.fifa_ranking,
            "elo_rating": team_b.stats.elo_rating,
            "form": f"{team_b.stats.wins_last_10}W-{team_b.stats.draws_last_10}D-{team_b.stats.losses_last_10}L",
            "form_last_5": team_b.stats.form_last_5,
            "xg_for": team_b.stats.xg_for_avg,
            "xg_against": team_b.stats.xg_against_avg,
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
    """Simulate group standings using Poisson predictions for unplayed matches."""
    teams = data_service.get_teams_by_group(group_letter.upper())
    if not teams:
        return []

    matches = data_service.load_matches(stage="group", group=group_letter.upper())

    standings: dict[str, GroupStanding] = {
        t.code: GroupStanding(team_code=t.code, team_name=t.name)
        for t in teams
    }

    for match in matches:
        home = data_service.get_team_by_code(match.home_team_code)
        away = data_service.get_team_by_code(match.away_team_code)
        if not home or not away:
            continue

        if match.home_score is not None and match.away_score is not None:
            h_goals, a_goals = match.home_score, match.away_score
        else:
            pred = predict_match_statistical(home, away, match)
            h_goals = pred["predicted_home_score"]
            a_goals = pred["predicted_away_score"]

        h = standings[home.code]
        a = standings[away.code]
        h.played += 1
        a.played += 1
        h.goals_for += h_goals
        h.goals_against += a_goals
        a.goals_for += a_goals
        a.goals_against += h_goals
        h.goal_difference = h.goals_for - h.goals_against
        a.goal_difference = a.goals_for - a.goals_against

        if h_goals > a_goals:
            h.won += 1
            h.points += 3
            a.lost += 1
        elif h_goals < a_goals:
            a.won += 1
            a.points += 3
            h.lost += 1
        else:
            h.drawn += 1
            a.drawn += 1
            h.points += 1
            a.points += 1

    sorted_standings = sorted(
        standings.values(),
        key=lambda s: (s.points, s.goal_difference, s.goals_for),
        reverse=True,
    )
    for idx, s in enumerate(sorted_standings, 1):
        s.position = idx

    return sorted_standings
