"""Pydantic models for user predictions and AI predictions."""

from datetime import datetime

from pydantic import BaseModel, Field


class MyPredictionCreate(BaseModel):
    """Payload for creating / updating a user prediction."""

    match_id: int = Field(..., description="Match ID to predict")
    predicted_home_score: int = Field(..., ge=0, description="Predicted home goals")
    predicted_away_score: int = Field(..., ge=0, description="Predicted away goals")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="User confidence 0-1")
    notes: str | None = Field(default=None, max_length=500, description="Optional user notes")


class MyPrediction(BaseModel):
    """A stored user prediction with computed points."""

    id: int | None = Field(default=None)
    match_id: int
    predicted_home_score: int = Field(..., ge=0)
    predicted_away_score: int = Field(..., ge=0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: str | None = None
    points_earned: int | None = Field(default=None, description="0, 1, or 3 points")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIPrediction(BaseModel):
    """An AI-generated match prediction."""

    match_id: int
    model_config = {"protected_namespaces": ()}
    model_used: str = Field(default="gemini-1.5-flash", description="LLM model identifier")
    predicted_home_score: int = Field(..., ge=0)
    predicted_away_score: int = Field(..., ge=0)
    home_win_prob: float = Field(..., ge=0.0, le=1.0, description="P(home win)")
    draw_prob: float = Field(..., ge=0.0, le=1.0, description="P(draw)")
    away_win_prob: float = Field(..., ge=0.0, le=1.0, description="P(away win)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence")
    analysis_text: str = Field(..., description="Narrative analysis of the match")
    factors: list[str] = Field(default_factory=list, description="Key factors in prediction")


class PredictionStats(BaseModel):
    """Aggregated statistics for user predictions."""

    total_predictions: int = 0
    matches_played: int = 0
    exact_scores: int = 0
    correct_outcomes: int = 0
    wrong: int = 0
    total_points: int = 0
    accuracy_pct: float = 0.0
    avg_confidence: float = 0.0


class PredictionResponse(BaseModel):
    """API response wrapper for prediction data."""

    success: bool = True
    data: MyPrediction | AIPrediction | PredictionStats | list[MyPrediction]
    count: int = 1
