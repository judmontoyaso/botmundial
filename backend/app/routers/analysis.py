"""Router for statistical / AI analysis endpoints."""

import time
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from app.services import analysis as analysis_service
from app.services import data_service
from app.services import llm_service
from app.services import predictor as predictor_service

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/match/{match_id}")
async def match_analysis(match_id: int):
    """Full match analysis combining statistical + LLM insights."""
    match = data_service.get_match_by_id(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    home = data_service.get_team_by_code(match.home_team_code)
    away = data_service.get_team_by_code(match.away_team_code)
    if not home or not away:
        raise HTTPException(status_code=404, detail="Team data not found")

    # Statistical analysis
    stat_pred = analysis_service.predict_match_statistical(home, away)
    comparison = analysis_service.compare_teams(home, away)

    # LLM narrative analysis
    narrative = llm_service.analyze_match(home, away, stat_pred)

    # Combined prediction
    ai_prediction = predictor_service.predict_match(match_id)

    # Bet suggestion
    bet_suggestion = predictor_service.suggest_polla_bet(match_id)

    return {
        "success": True,
        "match": data_service.enrich_match(match).model_dump(),
        "comparison": comparison,
        "statistical_prediction": stat_pred,
        "ai_prediction": ai_prediction.model_dump() if ai_prediction else None,
        "narrative_analysis": narrative,
        "polla_suggestion": bet_suggestion,
    }


@router.get("/team/{code}")
async def team_analysis(code: str):
    """Detailed analysis for a single team."""
    team = data_service.get_team_by_code(code.upper())
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team '{code.upper()}' not found")

    strength = analysis_service.calculate_team_strength(team)

    # Get group rivals and compare
    group_teams = data_service.get_teams_by_group(team.group_letter)
    rivals = [t for t in group_teams if t.code != team.code]
    comparisons = [analysis_service.compare_teams(team, rival) for rival in rivals]

    # Group matches
    matches = data_service.load_matches(stage="group", group=team.group_letter)
    team_matches = [
        data_service.enrich_match(m).model_dump()
        for m in matches
        if m.home_team_code == team.code or m.away_team_code == team.code
    ]

    # Group standings prediction
    standings = analysis_service.calculate_group_standings(team.group_letter)

    return {
        "success": True,
        "team": team.model_dump(),
        "strength_score": strength,
        "group_letter": team.group_letter,
        "group_rivals": [r.model_dump() for r in rivals],
        "comparisons": comparisons,
        "matches": team_matches,
        "predicted_standings": [s.model_dump() for s in standings],
    }


@router.get("/group/{letter}")
async def group_analysis(letter: str):
    """Full group analysis with predicted standings."""
    letter = letter.upper()
    if letter not in "ABCDEFGHIJKL" or len(letter) != 1:
        raise HTTPException(status_code=400, detail="Invalid group letter. Must be A-L.")

    teams = data_service.get_teams_by_group(letter)
    if not teams:
        raise HTTPException(status_code=404, detail=f"No teams found for group {letter}")

    # Strength scores
    strengths = {
        t.code: analysis_service.calculate_team_strength(t) for t in teams
    }

    # All group matches enriched
    matches = data_service.load_matches(stage="group", group=letter)
    enriched_matches = [data_service.enrich_match(m).model_dump() for m in matches]

    # Predicted standings
    standings = analysis_service.calculate_group_standings(letter)

    # Match-by-match predictions
    match_predictions = []
    for m in matches:
        home = data_service.get_team_by_code(m.home_team_code)
        away = data_service.get_team_by_code(m.away_team_code)
        if home and away:
            pred = analysis_service.predict_match_statistical(home, away)
            match_predictions.append({
                "match_number": m.match_number,
                "home_team": m.home_team_code,
                "away_team": m.away_team_code,
                **pred,
            })

    return {
        "success": True,
        "group_letter": letter,
        "teams": [t.model_dump() for t in teams],
        "strength_scores": strengths,
        "matches": enriched_matches,
        "match_predictions": match_predictions,
        "predicted_standings": [s.model_dump() for s in standings],
    }


# ---------------------------------------------------------------------------
# Monte Carlo tournament simulation — cached for 1 hour
# ---------------------------------------------------------------------------

_sim_cache: dict = {}
_SIM_TTL = 3600  # seconds


@router.get("/tournament/simulation")
async def tournament_simulation(n: int = Query(default=5000, ge=500, le=20000)):
    """
    Run Monte Carlo simulation of the full World Cup 2026.
    Returns probability of champion / finalist / top-4 / top-8 / group advance per team.
    Result is cached for 1 hour.
    """
    cache_key = n
    cached = _sim_cache.get(cache_key)
    if cached and (time.time() - cached["ts"]) < _SIM_TTL:
        return {"success": True, **cached["data"]}

    result = analysis_service.run_tournament_simulation(n_simulations=n)
    _sim_cache[cache_key] = {"ts": time.time(), "data": result}
    return {"success": True, **result}
