"""Combined predictor – merges Poisson statistical + LLM predictions."""

from __future__ import annotations

from typing import Optional

from app.models.prediction import AIPrediction
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
    """Polla scoring: 3 = exact score, 1 = correct outcome, 0 = wrong."""
    if predicted_home == actual_home and predicted_away == actual_away:
        return 3
    pred_outcome = 1 if predicted_home > predicted_away else (-1 if predicted_home < predicted_away else 0)
    actual_outcome = 1 if actual_home > actual_away else (-1 if actual_home < actual_away else 0)
    return 1 if pred_outcome == actual_outcome else 0


# ---------------------------------------------------------------------------
# Combined prediction
# ---------------------------------------------------------------------------

def predict_match(match_id: int) -> Optional[AIPrediction]:
    """
    Generate a combined prediction:
      - Checks Supabase cache first
      - Statistical Poisson model (60% weight on probs)
      - LLM correction (40% weight)
      - Caches result to Supabase
    """
    cached = data_service.get_ai_prediction(match_id)
    if cached is not None:
        return cached

    match = data_service.get_match_by_id(match_id)
    if match is None:
        return None

    home = data_service.get_team_by_code(match.home_team_code)
    away = data_service.get_team_by_code(match.away_team_code)
    if not home or not away:
        return None

    # Poisson statistical prediction
    stat = analysis_service.predict_match_statistical(home, away, match)

    # LLM prediction (uses enriched context)
    llm = llm_service.predict_match(home, away, stat, match)

    # Merge probabilities (60% stat / 40% LLM), validating the LLM output
    sw, lw = 0.6, 0.4

    def _llm_prob(key: str, default: float) -> float:
        try:
            v = float(llm.get(key, default))
        except (TypeError, ValueError):
            return default
        return min(max(v, 0.0), 1.0)

    home_win_prob = stat["home_win_prob"] * sw + _llm_prob("home_win_prob", stat["home_win_prob"]) * lw
    draw_prob = stat["draw_prob"] * sw + _llm_prob("draw_prob", stat["draw_prob"]) * lw
    away_win_prob = stat["away_win_prob"] * sw + _llm_prob("away_win_prob", stat["away_win_prob"]) * lw

    # Normalise so the three probabilities sum exactly to 1
    prob_total = home_win_prob + draw_prob + away_win_prob
    if prob_total > 0:
        home_win_prob = round(home_win_prob / prob_total, 4)
        away_win_prob = round(away_win_prob / prob_total, 4)
        draw_prob = round(1.0 - home_win_prob - away_win_prob, 4)

    # Score: most probable scoreline CONSISTENT with the merged outcome,
    # taken from the Poisson matrix — score, probabilities and confidence
    # always tell the same story.
    outcome = analysis_service.predicted_outcome(home_win_prob, draw_prob, away_win_prob)
    merged_home, merged_away = analysis_service.most_likely_score_for_outcome(
        stat["scoreline_matrix"], outcome
    )

    confidence = analysis_service.outcome_confidence(home_win_prob, draw_prob, away_win_prob)

    analysis_text = llm.get(
        "analysis_text",
        f"Predicción combinada para {home.name} vs {away.name}: {merged_home}-{merged_away}.",
    )
    factors = llm.get("factors", [])

    from app.config import get_settings as _get_settings
    pred = AIPrediction(
        match_id=match_id,
        model_used=f"{_get_settings().DEEPSEEK_MODEL} + poisson",
        predicted_home_score=merged_home,
        predicted_away_score=merged_away,
        home_win_prob=home_win_prob,
        draw_prob=draw_prob,
        away_win_prob=away_win_prob,
        confidence_score=confidence,
        analysis_text=analysis_text,
        factors=factors,
        poisson_home_lambda=stat["poisson_home_lambda"],
        poisson_away_lambda=stat["poisson_away_lambda"],
        scoreline_matrix=stat["scoreline_matrix"],
    )

    data_service.save_ai_prediction(pred)
    return pred


# ---------------------------------------------------------------------------
# Bulk pregeneration & refresh
# ---------------------------------------------------------------------------

def pregenerate_predictions(limit: Optional[int] = None) -> dict:
    """
    Generate and cache AI predictions for all upcoming scheduled matches,
    in chronological order. Matches that already have a cached prediction
    are skipped, so this is cheap to call repeatedly (startup, post-sync).
    """
    import logging
    logger = logging.getLogger("app.services.predictor")

    matches = [m for m in data_service.load_matches() if m.status.value == "scheduled"]
    matches.sort(key=lambda m: str(m.match_date))
    if limit:
        matches = matches[:limit]

    cached_ids = set(data_service.get_all_ai_predictions().keys())
    generated = skipped = errors = 0
    for m in matches:
        if m.id in cached_ids:
            skipped += 1
            continue
        try:
            if predict_match(m.id) is not None:
                generated += 1
                logger.info(
                    "Pre-generated prediction %s vs %s (match %d)",
                    m.home_team_code, m.away_team_code, m.id,
                )
            else:
                errors += 1
        except Exception as exc:
            errors += 1
            logger.warning("Pregeneration failed for match %d: %s", m.id, exc)

    return {"generated": generated, "cached": skipped, "errors": errors}


def refresh_predictions_for_teams(team_codes: set[str]) -> int:
    """
    After real results change ELO/form, regenerate cached AI predictions
    for every upcoming match involving the affected teams.
    """
    from app.services import llm_service

    refreshed = 0
    for m in data_service.load_matches():
        if m.status.value != "scheduled":
            continue
        if m.home_team_code not in team_codes and m.away_team_code not in team_codes:
            continue
        data_service.delete_ai_prediction(m.id)
        # Drop stale in-memory LLM cache entries for this match
        stale = [
            k for k in list(llm_service._cache)
            if k.endswith(f"_{m.id}")
            or k == f"analysis_{m.home_team_code}_{m.away_team_code}"
        ]
        for k in stale:
            llm_service._cache.pop(k, None)
        try:
            if predict_match(m.id) is not None:
                refreshed += 1
        except Exception:
            pass
    return refreshed


# ---------------------------------------------------------------------------
# Polla bet suggestions
# ---------------------------------------------------------------------------

def suggest_polla_bet(match_id: int) -> Optional[dict]:
    """Return safe_bet (most likely outcome) and value_bet (exact score 3pts)."""
    prediction = predict_match(match_id)
    if prediction is None:
        return None

    match = data_service.get_match_by_id(match_id)
    home = data_service.get_team_by_code(match.home_team_code) if match else None
    away = data_service.get_team_by_code(match.away_team_code) if match else None

    probs = {
        "home_win": prediction.home_win_prob,
        "draw": prediction.draw_prob,
        "away_win": prediction.away_win_prob,
    }
    best_outcome = max(probs, key=probs.get)  # type: ignore[arg-type]

    if best_outcome == "home_win":
        safe_score = {"home": 1, "away": 0}
        outcome_label = f"{home.name} gana" if home else "Local gana"
    elif best_outcome == "away_win":
        safe_score = {"home": 0, "away": 1}
        outcome_label = f"{away.name} gana" if away else "Visitante gana"
    else:
        safe_score = {"home": 1, "away": 1}
        outcome_label = "Empate"

    # Find most probable exact score from matrix
    matrix = prediction.scoreline_matrix
    if matrix:
        best_h, best_a = 0, 0
        best_p = -1.0
        for h, row in enumerate(matrix):
            for a, p in enumerate(row):
                if p > best_p:
                    best_p = p
                    best_h, best_a = h, a
        value_home, value_away = best_h, best_a
    else:
        value_home = prediction.predicted_home_score
        value_away = prediction.predicted_away_score

    return {
        "match_id": match_id,
        "home_team": home.name if home else "?",
        "away_team": away.name if away else "?",
        "poisson_home_lambda": prediction.poisson_home_lambda,
        "poisson_away_lambda": prediction.poisson_away_lambda,
        "safe_bet": {
            "predicted_home_score": safe_score["home"],
            "predicted_away_score": safe_score["away"],
            "outcome": outcome_label,
            "probability": probs[best_outcome],
            "expected_points": round(probs[best_outcome] * 1, 3),
            "reasoning": f"Resultado más probable ({probs[best_outcome]:.0%}). Apunta a 1 punto seguro.",
        },
        "value_bet": {
            "predicted_home_score": value_home,
            "predicted_away_score": value_away,
            "outcome": f"{value_home}-{value_away}",
            "confidence": prediction.confidence_score,
            "expected_points": round(prediction.confidence_score * 3, 3),
            "reasoning": "Marcador exacto más probable según Poisson. Mayor riesgo pero 3 puntos si acierta.",
        },
        "ai_prediction": prediction.model_dump(),
    }
