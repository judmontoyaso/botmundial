"""Data service – loads teams, matches and manages in-memory predictions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.match import Match, MatchStatus, MatchWithTeams
from app.models.prediction import MyPrediction, MyPredictionCreate
from app.models.team import Team

# ---------------------------------------------------------------------------
# Module-level data store (singleton pattern)
# ---------------------------------------------------------------------------
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_teams: list[Team] = []
_matches: list[Match] = []
_predictions: list[MyPrediction] = []
_next_prediction_id: int = 1
_teams_by_code: dict[str, Team] = {}


def _ensure_loaded() -> None:
    """Lazily load JSON data on first access."""
    if not _teams:
        _load_teams()
    if not _matches:
        _load_matches()


# ---------------------------------------------------------------------------
# Team helpers
# ---------------------------------------------------------------------------

def _load_teams() -> None:
    global _teams, _teams_by_code
    path = _DATA_DIR / "teams.json"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    _teams = [Team(id=idx + 1, **t) for idx, t in enumerate(raw)]
    _teams_by_code = {t.code: t for t in _teams}


def load_teams() -> list[Team]:
    """Return all 48 teams."""
    _ensure_loaded()
    return list(_teams)


def get_team_by_code(code: str) -> Optional[Team]:
    """Find a team by its 3-letter FIFA code (case-insensitive)."""
    _ensure_loaded()
    return _teams_by_code.get(code.upper())


def get_teams_by_group(letter: str) -> list[Team]:
    """Return the four teams in a given group."""
    _ensure_loaded()
    letter = letter.upper()
    return [t for t in _teams if t.group_letter == letter]


# ---------------------------------------------------------------------------
# Match helpers
# ---------------------------------------------------------------------------

def _load_matches() -> None:
    global _matches
    path = _DATA_DIR / "schedule.json"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    _matches = [
        Match(
            id=m["match_number"],
            match_number=m["match_number"],
            stage=m["stage"],
            group_letter=m.get("group_letter"),
            home_team_code=m["home_team"],
            away_team_code=m["away_team"],
            match_date=m["match_date"],
            venue=m["venue"],
            city=m["city"],
            status=m.get("status", "scheduled"),
        )
        for m in raw
    ]


def load_matches(
    stage: Optional[str] = None,
    group: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Match]:
    """Return matches with optional filters."""
    _ensure_loaded()
    result = list(_matches)
    if stage:
        result = [m for m in result if m.stage.value == stage]
    if group:
        result = [m for m in result if m.group_letter and m.group_letter.upper() == group.upper()]
    if status:
        result = [m for m in result if m.status.value == status]
    return result


def get_match_by_id(match_id: int) -> Optional[Match]:
    """Find a match by its ID / match_number."""
    _ensure_loaded()
    for m in _matches:
        if m.id == match_id:
            return m
    return None


def get_upcoming_matches(limit: int = 5) -> list[Match]:
    """Return the next N upcoming (scheduled) matches sorted by date."""
    _ensure_loaded()
    now = datetime.now(timezone.utc)
    upcoming = [
        m for m in _matches
        if m.status == MatchStatus.SCHEDULED and m.match_date >= now
    ]
    upcoming.sort(key=lambda m: m.match_date)
    return upcoming[:limit]


def enrich_match(match: Match) -> MatchWithTeams:
    """Add team names / flags to a match for display."""
    _ensure_loaded()
    home = _teams_by_code.get(match.home_team_code)
    away = _teams_by_code.get(match.away_team_code)
    return MatchWithTeams(
        match=match,
        home_team_name=home.name if home else match.home_team_code,
        away_team_name=away.name if away else match.away_team_code,
        home_team_flag=home.flag_emoji if home else "",
        away_team_flag=away.flag_emoji if away else "",
        home_team_ranking=home.fifa_ranking if home else 0,
        away_team_ranking=away.fifa_ranking if away else 0,
    )


def update_match_result(match_id: int, home_score: int, away_score: int) -> Optional[Match]:
    """Set the result for a match and mark it completed."""
    _ensure_loaded()
    match = get_match_by_id(match_id)
    if match is None:
        return None
    match.home_score = home_score
    match.away_score = away_score
    match.status = MatchStatus.COMPLETED
    # Recalculate points for predictions on this match
    _recalculate_prediction_points(match)
    return match


# ---------------------------------------------------------------------------
# Prediction helpers (in-memory store)
# ---------------------------------------------------------------------------

def save_prediction(data: MyPredictionCreate) -> MyPrediction:
    """Create or update a prediction for a match."""
    global _next_prediction_id

    # Check for existing prediction on the same match
    existing = next((p for p in _predictions if p.match_id == data.match_id), None)
    if existing:
        existing.predicted_home_score = data.predicted_home_score
        existing.predicted_away_score = data.predicted_away_score
        existing.confidence = data.confidence
        existing.notes = data.notes
        return existing

    pred = MyPrediction(
        id=_next_prediction_id,
        match_id=data.match_id,
        predicted_home_score=data.predicted_home_score,
        predicted_away_score=data.predicted_away_score,
        confidence=data.confidence,
        notes=data.notes,
    )
    _next_prediction_id += 1
    _predictions.append(pred)
    return pred


def get_predictions() -> list[MyPrediction]:
    """Return all stored predictions."""
    return list(_predictions)


def get_prediction_by_match(match_id: int) -> Optional[MyPrediction]:
    """Return prediction for a specific match."""
    return next((p for p in _predictions if p.match_id == match_id), None)


def _recalculate_prediction_points(match: Match) -> None:
    """Update points_earned for predictions matching a completed match."""
    if match.home_score is None or match.away_score is None:
        return
    for pred in _predictions:
        if pred.match_id == match.id:
            pred.points_earned = _calculate_points(
                pred.predicted_home_score,
                pred.predicted_away_score,
                match.home_score,
                match.away_score,
            )


def _calculate_points(ph: int, pa: int, ah: int, aa: int) -> int:
    """Polla scoring: 3 = exact, 1 = correct outcome, 0 = wrong."""
    if ph == ah and pa == aa:
        return 3
    # Determine outcomes
    pred_outcome = (1 if ph > pa else (-1 if ph < pa else 0))
    actual_outcome = (1 if ah > aa else (-1 if ah < aa else 0))
    if pred_outcome == actual_outcome:
        return 1
    return 0
