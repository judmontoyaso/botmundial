"""Combined predictor – merges statistical + LLM predictions."""

from __future__ import annotations

from typing import Optional

from app.models.prediction import AIPrediction
from app.models.team import Team
from app.services import analysis as analysis_service
from app.services import data_service
from app.services import llm_service


# ---------------------------------------------------------------------------
# Points calculation
# ---------------------------------------------------------------------------

def calculate_points(
    predicted_home: int,
    predicted_away: int,
    actual_home: int,
    actual_away: int,
) -> int:
    """
    Polla scoring system:
        3 points – exact score match
        1 point  – correct outcome (win / draw)
        0 points – incorrect
    """
    if predicted_home == actual_home and predicted_away == actual_away:
        return 3

    pred_outcome = (
        1 if predicted_home > predicted_away
        else (-1 if predicted_home < predicted_away else 0)
    )
    actual_outcome = (
        1 if actual_home > actual_away
        else (-1 if actual_home < actual_away else 0)
    )
    if pred_outcome == actual_outcome:
        return 1
    return 0


# ---------------------------------------------------------------------------
# Combined prediction
# ---------------------------------------------------------------------------

def predict_match(match_id: int) -> Optional[AIPrediction]:
    """
    Generate a combined prediction for a match by merging:
      - Statistical model output (60% weight)
      - LLM output (40% weight)
    First checks if a cached prediction exists in the database.
    """
    # 1. Check Supabase database cache first
    cached = data_service.get_ai_prediction(match_id)
    if cached is not None:
        return cached

    # 2. Generate new prediction if not cached
    match = data_service.get_match_by_id(match_id)
    if match is None:
        return None

    home = data_service.get_team_by_code(match.home_team_code)
    away = data_service.get_team_by_code(match.away_team_code)
    if not home or not away:
        return None

    # Statistical prediction
    stat = analysis_service.predict_match_statistical(home, away, match)

    # LLM prediction
    llm = llm_service.predict_match(home, away, stat, match)

    # Merge scores (weighted average, round to int)
    stat_weight = 0.6
    llm_weight = 0.4

    merged_home = round(
        stat["predicted_home_score"] * stat_weight
        + llm.get("predicted_home_score", stat["predicted_home_score"]) * llm_weight
    )
    merged_away = round(
        stat["predicted_away_score"] * stat_weight
        + llm.get("predicted_away_score", stat["predicted_away_score"]) * llm_weight
    )

    # Merge probabilities
    home_win_prob = round(
        stat["home_win_prob"] * stat_weight
        + llm.get("home_win_prob", stat["home_win_prob"]) * llm_weight, 3
    )
    draw_prob = round(
        stat["draw_prob"] * stat_weight
        + llm.get("draw_prob", stat["draw_prob"]) * llm_weight, 3
    )
    away_win_prob = round(
        stat["away_win_prob"] * stat_weight
        + llm.get("away_win_prob", stat["away_win_prob"]) * llm_weight, 3
    )

    # Normalise probabilities
    prob_total = home_win_prob + draw_prob + away_win_prob
    if prob_total > 0:
        home_win_prob = round(home_win_prob / prob_total, 3)
        draw_prob = round(draw_prob / prob_total, 3)
        away_win_prob = round(away_win_prob / prob_total, 3)

    confidence = round(
        stat["confidence"] * stat_weight
        + llm.get("confidence_score", stat["confidence"]) * llm_weight, 3
    )

    analysis_text = llm.get(
        "analysis_text",
        f"Combined prediction for {home.name} vs {away.name}: {merged_home}-{merged_away}.",
    )
    factors = llm.get("factors", [])

    pred = AIPrediction(
        match_id=match_id,
        model_used="gemini-1.5-flash + statistical",
        predicted_home_score=max(0, merged_home),
        predicted_away_score=max(0, merged_away),
        home_win_prob=home_win_prob,
        draw_prob=draw_prob,
        away_win_prob=away_win_prob,
        confidence_score=confidence,
        analysis_text=analysis_text,
        factors=factors,
    )

    # 3. Cache generated prediction in Supabase database
    data_service.save_ai_prediction(pred)

    return pred


# ---------------------------------------------------------------------------
# Polla bet suggestions
# ---------------------------------------------------------------------------

def suggest_polla_bet(match_id: int) -> Optional[dict]:
    """
    Return two betting suggestions:
      - safe_bet:  most likely outcome (best chance of 1 pt)
      - value_bet: exact score for 3 pts upside
    """
    prediction = predict_match(match_id)
    if prediction is None:
        return None

    match = data_service.get_match_by_id(match_id)
    home = data_service.get_team_by_code(match.home_team_code) if match else None
    away = data_service.get_team_by_code(match.away_team_code) if match else None

    # Determine most likely outcome for safe bet
    probs = {
        "home_win": prediction.home_win_prob,
        "draw": prediction.draw_prob,
        "away_win": prediction.away_win_prob,
    }
    best_outcome = max(probs, key=probs.get)  # type: ignore[arg-type]

    if best_outcome == "home_win":
        safe_score = {"home": 1, "away": 0}
        outcome_label = f"{home.name} win" if home else "Home win"
    elif best_outcome == "away_win":
        safe_score = {"home": 0, "away": 1}
        outcome_label = f"{away.name} win" if away else "Away win"
    else:
        safe_score = {"home": 1, "away": 1}
        outcome_label = "Draw"

    return {
        "match_id": match_id,
        "home_team": home.name if home else "?",
        "away_team": away.name if away else "?",
        "safe_bet": {
            "predicted_home_score": safe_score["home"],
            "predicted_away_score": safe_score["away"],
            "outcome": outcome_label,
            "probability": probs[best_outcome],
            "expected_points": round(probs[best_outcome] * 1, 2),
            "reasoning": f"Most likely outcome ({probs[best_outcome]:.0%} probability). Targets 1 point.",
        },
        "value_bet": {
            "predicted_home_score": prediction.predicted_home_score,
            "predicted_away_score": prediction.predicted_away_score,
            "outcome": f"{prediction.predicted_home_score}-{prediction.predicted_away_score}",
            "confidence": prediction.confidence_score,
            "expected_points": round(prediction.confidence_score * 3, 2),
            "reasoning": f"AI-predicted exact score. Higher risk for 3 points if correct.",
        },
        "ai_prediction": prediction.model_dump(),
    }
