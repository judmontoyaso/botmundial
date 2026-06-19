"""Router for user predictions and AI predictions."""

import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.models.prediction import (
    AIPrediction,
    MyPrediction,
    MyPredictionCreate,
    PredictionResponse,
    PredictionStats,
)
from app.services import accuracy as accuracy_service
from app.services import data_service
from app.services import predictor as predictor_service

router = APIRouter(prefix="/predictions", tags=["Predictions"])

# Short-TTL cache for the AI accuracy report — recomputed as live results arrive.
_accuracy_cache: dict = {}
_ACCURACY_TTL = 900  # 15 minutes


@router.get("", response_model=PredictionResponse)
async def list_predictions():
    """Return all user predictions."""
    preds = data_service.get_predictions()
    return PredictionResponse(data=preds, count=len(preds))


@router.post("", response_model=PredictionResponse, status_code=201)
async def save_prediction(payload: MyPredictionCreate):
    """Create or update a prediction for a match."""
    # Validate match exists
    match = data_service.get_match_by_id(payload.match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match {payload.match_id} not found")
    pred = data_service.save_prediction(payload)
    return PredictionResponse(data=pred, count=1)


@router.get("/stats", response_model=PredictionResponse)
async def prediction_stats():
    """Return aggregated stats for user predictions."""
    preds = data_service.get_predictions()
    total = len(preds)
    scored = [p for p in preds if p.points_earned is not None]
    exact = sum(1 for p in scored if p.points_earned == 3)
    correct = sum(1 for p in scored if p.points_earned == 1)
    wrong = sum(1 for p in scored if p.points_earned == 0)
    total_pts = sum(p.points_earned for p in scored if p.points_earned is not None)
    avg_conf = (sum(p.confidence for p in preds) / total) if total > 0 else 0.0
    accuracy = ((exact + correct) / len(scored) * 100) if scored else 0.0

    stats = PredictionStats(
        total_predictions=total,
        matches_played=len(scored),
        exact_scores=exact,
        correct_outcomes=correct,
        wrong=wrong,
        total_points=total_pts,
        accuracy_pct=round(accuracy, 1),
        avg_confidence=round(avg_conf, 2),
    )
    return PredictionResponse(data=stats, count=1)


@router.delete("/{prediction_id}", status_code=204)
async def delete_prediction(prediction_id: int):
    """Delete a user prediction by its ID."""
    deleted = data_service.delete_prediction(prediction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Prediction {prediction_id} not found")


@router.get("/ai/accuracy")
async def ai_accuracy(refresh: bool = Query(default=False, description="Bypass the cache")):
    """
    Effectiveness of the AI predictions against already-played matches:
    outcome accuracy, exact-score hits, polla points, calibration and a
    match-by-match breakdown. Cached for 15 min; updates as real results arrive.
    """
    cached = _accuracy_cache.get("data")
    if cached and not refresh and (time.time() - cached["ts"]) < _ACCURACY_TTL:
        return {"success": True, **cached["data"]}

    data = accuracy_service.compute_ai_accuracy()
    _accuracy_cache["data"] = {"ts": time.time(), "data": data}
    return {"success": True, **data}


@router.post("/ai/pregenerate")
async def pregenerate_ai_predictions(
    background: BackgroundTasks,
    limit: int | None = Query(default=None, ge=1, le=104),
):
    """
    Pre-generate AI predictions for all upcoming matches (skips cached).
    Runs in background; check /predictions to see results appear.
    """
    background.add_task(predictor_service.pregenerate_predictions, limit)
    return {"success": True, "message": "Pregeneración de predicciones iniciada en segundo plano"}


@router.get("/ai/{match_id}", response_model=PredictionResponse)
async def get_ai_prediction(
    match_id: int,
    force: bool = Query(default=False, description="Force regenerate even if cached"),
):
    """Get a combined AI + statistical prediction. Pass force=true to refresh from DeepSeek."""
    if force:
        data_service.delete_ai_prediction(match_id)
        # Clear all in-memory LLM cache entries that reference this match_id.
        # Keys use format "prediction_{home}_{away}_{match_id}" and "analysis_{home}_{away}",
        # so we drop every key ending with the match_id or containing it as a suffix segment.
        from app.services import llm_service
        stale = [k for k in list(llm_service._cache) if k.endswith(f"_{match_id}")]
        for k in stale:
            llm_service._cache.pop(k, None)
    prediction = predictor_service.predict_match(match_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found or teams missing")
    return PredictionResponse(data=prediction, count=1)
