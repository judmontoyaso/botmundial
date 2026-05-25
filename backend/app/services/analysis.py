"""Statistical analysis service for teams and matches."""

from __future__ import annotations

from typing import Optional

from app.models.match import Match
from app.models.team import GroupStanding, Team
from app.services import data_service


# ---------------------------------------------------------------------------
# Team strength score (0-100)
# ---------------------------------------------------------------------------

def calculate_team_strength(team: Team) -> float:
    """
    Compute an overall strength score for a team on a 0-100 scale.

    Weighted formula:
        ranking  (40%) – lower rank = stronger
        form     (30%) – wins / draws / losses in last 10
        goals    (20%) – scoring & defensive averages
        experience (10%) – World Cup appearances
    """
    # --- Ranking component (40 pts max) ---
    # Rank 1 → 40, rank 48 → ~7
    ranking_score = max(0, 40 * (1 - (team.fifa_ranking - 1) / 47))

    # --- Form component (30 pts max) ---
    stats = team.stats
    form_score = 30 * (stats.wins_last_10 * 3 + stats.draws_last_10) / 30  # max 30 pts from 10W

    # --- Goals component (20 pts max) ---
    attack = min(stats.goals_scored_avg / 2.5, 1.0) * 10  # max 10
    defense = max(0, 1 - stats.goals_conceded_avg / 2.0) * 10  # max 10
    goals_score = attack + defense

    # --- Experience component (10 pts max) ---
    exp_score = min(stats.world_cup_appearances / 20, 1.0) * 10

    total = ranking_score + form_score + goals_score + exp_score
    return round(min(max(total, 0), 100), 1)


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
            "form": f"{team_a.stats.wins_last_10}W-{team_a.stats.draws_last_10}D-{team_a.stats.losses_last_10}L",
            "goals_avg": team_a.stats.goals_scored_avg,
            "conceded_avg": team_a.stats.goals_conceded_avg,
        },
        "team_b": {
            "code": team_b.code,
            "name": team_b.name,
            "strength": str_b,
            "fifa_ranking": team_b.fifa_ranking,
            "form": f"{team_b.stats.wins_last_10}W-{team_b.stats.draws_last_10}D-{team_b.stats.losses_last_10}L",
            "goals_avg": team_b.stats.goals_scored_avg,
            "conceded_avg": team_b.stats.goals_conceded_avg,
        },
        "advantage": team_a.code if str_a >= str_b else team_b.code,
        "strength_diff": round(abs(str_a - str_b), 1),
        "a_win_pct": round(str_a / total * 100, 1),
        "b_win_pct": round(str_b / total * 100, 1),
    }


# ---------------------------------------------------------------------------
# Climate and Location Modifiers
# ---------------------------------------------------------------------------

CITY_CLIMATES = {
    "Mexico City": {"type": "altitude", "desc": "Alta Altitud / Cálido", "temp": 25},
    "Guadalajara": {"type": "altitude", "desc": "Altitud Moderada / Cálido", "temp": 28},
    "Monterrey": {"type": "hot_humid", "desc": "Muy Caluroso / Húmedo", "temp": 34},
    "Miami": {"type": "hot_humid", "desc": "Caluroso / Muy Húmedo", "temp": 31},
    "Houston": {"type": "hot_humid", "desc": "Caluroso / Húmedo", "temp": 33},
    "Dallas": {"type": "hot", "desc": "Muy Caluroso", "temp": 34},
    "Arlington": {"type": "hot", "desc": "Muy Caluroso", "temp": 34},
    "Atlanta": {"type": "hot_humid", "desc": "Caluroso / Húmedo", "temp": 31},
    "Kansas City": {"type": "warm", "desc": "Cálido", "temp": 29},
    "Philadelphia": {"type": "warm", "desc": "Cálido", "temp": 27},
    "New York": {"type": "warm", "desc": "Cálido", "temp": 26},
    "East Rutherford": {"type": "warm", "desc": "Cálido", "temp": 26},
    "Boston": {"type": "warm", "desc": "Cálido", "temp": 25},
    "Foxborough": {"type": "warm", "desc": "Cálido", "temp": 25},
    "Los Angeles": {"type": "warm", "desc": "Cálido / Seco", "temp": 26},
    "Santa Clara": {"type": "warm", "desc": "Cálido", "temp": 25},
    "San Francisco": {"type": "mild", "desc": "Templado", "temp": 20},
    "Seattle": {"type": "mild", "desc": "Templado", "temp": 22},
    "Vancouver": {"type": "mild", "desc": "Templado", "temp": 21},
    "Toronto": {"type": "mild", "desc": "Templado", "temp": 24},
}

def get_climate_modifier(team: Team, city: str) -> float:
    """Return a strength modifier (-5 to +5) based on team adaptation to city climate."""
    if city not in CITY_CLIMATES:
        return 0.0
    
    climate = CITY_CLIMATES[city]["type"]
    confed = team.confederation.upper()
    
    # Altitude: CONMEBOL and CONCACAF teams are more used to it.
    if climate == "altitude":
        if confed in ["CONMEBOL", "CONCACAF"]:
            return 3.0
        elif confed in ["UEFA"]:
            return -4.0
        else:
            return -2.0
            
    # Hot/Humid: CAF, CONMEBOL, CONCACAF adapt better than UEFA.
    if climate in ["hot_humid", "hot"]:
        if confed in ["CAF", "CONMEBOL", "CONCACAF"]:
            return 2.5
        elif confed == "UEFA":
            return -3.0
        else:
            return 0.0
            
    # Mild: UEFA teams perform optimally without heat exhaustion
    if climate == "mild":
        if confed == "UEFA":
            return 2.0
        else:
            return 0.0
            
    return 0.0

def get_continent_advantage(team: Team) -> float:
    """Home continent advantage for CONCACAF/CONMEBOL in NA."""
    # US, Mexico, Canada host the tournament. Americas teams have massive support.
    if team.confederation.upper() == "CONCACAF":
        return 5.0
    elif team.confederation.upper() == "CONMEBOL":
        return 3.0
    return 0.0

# ---------------------------------------------------------------------------
# Statistical match prediction
# ---------------------------------------------------------------------------

def predict_match_statistical(home_team: Team, away_team: Team, match: Optional[Match] = None) -> dict:
    """
    Generate a purely statistical prediction for a match.

    Returns predicted score, win/draw/loss probabilities, confidence, and environmental factors.
    """
    str_home_base = calculate_team_strength(home_team)
    str_away_base = calculate_team_strength(away_team)

    home_climate_mod = 0.0
    away_climate_mod = 0.0
    home_cont_mod = get_continent_advantage(home_team)
    away_cont_mod = get_continent_advantage(away_team)
    
    city = ""
    climate_desc = ""
    if match and match.city:
        city = match.city
        home_climate_mod = get_climate_modifier(home_team, city)
        away_climate_mod = get_climate_modifier(away_team, city)
        if city in CITY_CLIMATES:
            climate_desc = CITY_CLIMATES[city]["desc"]

    str_home = str_home_base + home_climate_mod + home_cont_mod
    str_away = str_away_base + away_climate_mod + away_cont_mod

    # Default Home advantage bonus (+3 strength points) since "Home" team on paper has a slight edge
    str_home_adj = str_home + 3
    total = str_home_adj + str_away if (str_home_adj + str_away) > 0 else 1

    home_ratio = str_home_adj / total
    away_ratio = str_away / total

    # Probabilities (simplified model)
    home_win_prob = round(home_ratio * 0.85, 3)  # scale down for draw room
    away_win_prob = round(away_ratio * 0.85, 3)
    draw_prob = round(max(0.05, 1.0 - home_win_prob - away_win_prob), 3)

    # Normalise
    prob_total = home_win_prob + draw_prob + away_win_prob
    home_win_prob = round(home_win_prob / prob_total, 3)
    draw_prob = round(draw_prob / prob_total, 3)
    away_win_prob = round(away_win_prob / prob_total, 3)

    # Predicted goals (weighted avg of attacking / defending strengths)
    # Give a slight bump to goals if playing in altitude (ball moves faster)
    goal_multiplier = 1.1 if city in CITY_CLIMATES and CITY_CLIMATES[city]["type"] == "altitude" else 1.0
    
    home_goals = round(
        (home_team.stats.goals_scored_avg * 0.6 + away_team.stats.goals_conceded_avg * 0.4) * goal_multiplier, 1
    )
    away_goals = round(
        (away_team.stats.goals_scored_avg * 0.6 + home_team.stats.goals_conceded_avg * 0.4) * goal_multiplier, 1
    )

    # Round to nearest int for scoreline
    pred_home = max(0, round(home_goals))
    pred_away = max(0, round(away_goals))

    # Confidence based on strength difference
    strength_diff = abs(str_home - str_away)
    confidence = round(min(0.5 + strength_diff / 100, 0.95), 2)

    return {
        "predicted_home_score": pred_home,
        "predicted_away_score": pred_away,
        "home_win_prob": home_win_prob,
        "draw_prob": draw_prob,
        "away_win_prob": away_win_prob,
        "confidence": confidence,
        "home_strength": round(str_home_base, 1),
        "away_strength": round(str_away_base, 1),
        "home_climate_mod": home_climate_mod,
        "away_climate_mod": away_climate_mod,
        "home_cont_mod": home_cont_mod,
        "away_cont_mod": away_cont_mod,
        "city": city,
        "climate_desc": climate_desc,
        "home_goals_expected": home_goals,
        "away_goals_expected": away_goals,
    }


# ---------------------------------------------------------------------------
# Group standings prediction
# ---------------------------------------------------------------------------

def calculate_group_standings(group_letter: str) -> list[GroupStanding]:
    """
    Simulate group standings based on statistical predictions for
    all matches in the group.
    """
    teams = data_service.get_teams_by_group(group_letter.upper())
    if not teams:
        return []

    matches = data_service.load_matches(stage="group", group=group_letter.upper())

    # Initialise standings
    standings: dict[str, GroupStanding] = {}
    for t in teams:
        standings[t.code] = GroupStanding(
            team_code=t.code,
            team_name=t.name,
        )

    for match in matches:
        home = data_service.get_team_by_code(match.home_team_code)
        away = data_service.get_team_by_code(match.away_team_code)
        if not home or not away:
            continue

        # Use actual result if completed, otherwise predict
        if match.home_score is not None and match.away_score is not None:
            h_goals = match.home_score
            a_goals = match.away_score
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

    # Sort: points desc → GD desc → GF desc
    sorted_standings = sorted(
        standings.values(),
        key=lambda s: (s.points, s.goal_difference, s.goals_for),
        reverse=True,
    )
    for idx, s in enumerate(sorted_standings, 1):
        s.position = idx

    return sorted_standings
