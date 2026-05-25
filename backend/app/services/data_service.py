"""Data service – loads teams, matches and predictions from Supabase database with fallback."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.match import Match, MatchStatus, MatchWithTeams
from app.models.prediction import MyPrediction, MyPredictionCreate, AIPrediction
from app.models.team import Team
from app.supabase_client import supabase

logger = logging.getLogger("app.services.data_service")

# ---------------------------------------------------------------------------
# Module-level data store (fallback singleton pattern)
# ---------------------------------------------------------------------------
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_teams: list[Team] = []
_matches: list[Match] = []
_predictions: list[MyPrediction] = []
_next_prediction_id: int = 1
_teams_by_code: dict[str, Team] = {}


def _ensure_loaded() -> None:
    """Lazily load JSON data on first access if not using database."""
    if supabase is not None:
        return
    global _teams, _matches
    if not _teams:
        _load_teams_json()
    if not _matches:
        _load_matches_json()


def _load_teams_json() -> None:
    global _teams, _teams_by_code
    path = _DATA_DIR / "teams.json"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    _teams = [Team(id=idx + 1, **t) for idx, t in enumerate(raw)]
    _teams_by_code = {t.code: t for t in _teams}


def _load_matches_json() -> None:
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

# ---------------------------------------------------------------------------
# Team helpers
# ---------------------------------------------------------------------------

def load_teams() -> list[Team]:
    """Return all 48 teams from Supabase database (with JSON fallback)."""
    if supabase is not None:
        try:
            response = supabase.table("teams").select("*").execute()
            teams = []
            for t in response.data:
                teams.append(Team(
                    id=t["id"],
                    name=t["name"],
                    code=t["code"],
                    group_letter=t["group_letter"],
                    fifa_ranking=t["fifa_ranking"],
                    confederation=t["confederation"],
                    flag_emoji=t["flag_emoji"],
                    stats=t["stats"]
                ))
            return teams
        except Exception as e:
            logger.error(f"Error loading teams from Supabase: {e}. Falling back to JSON.")
    
    _ensure_loaded()
    return list(_teams)


def get_team_by_code(code: str) -> Optional[Team]:
    """Find a team by its 3-letter FIFA code (case-insensitive) from Supabase or JSON."""
    if supabase is not None:
        try:
            response = supabase.table("teams").select("*").eq("code", code.upper()).execute()
            if response.data:
                t = response.data[0]
                return Team(
                    id=t["id"],
                    name=t["name"],
                    code=t["code"],
                    group_letter=t["group_letter"],
                    fifa_ranking=t["fifa_ranking"],
                    confederation=t["confederation"],
                    flag_emoji=t["flag_emoji"],
                    stats=t["stats"]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting team {code} from Supabase: {e}. Falling back to JSON.")
    
    _ensure_loaded()
    # Cache lookup
    global _teams_by_code
    if not _teams_by_code and _teams:
        _teams_by_code = {t.code: t for t in _teams}
    return _teams_by_code.get(code.upper())


def get_teams_by_group(letter: str) -> list[Team]:
    """Return the four teams in a given group from Supabase or JSON."""
    if supabase is not None:
        try:
            response = supabase.table("teams").select("*").eq("group_letter", letter.upper()).execute()
            return [Team(
                id=t["id"],
                name=t["name"],
                code=t["code"],
                group_letter=t["group_letter"],
                fifa_ranking=t["fifa_ranking"],
                confederation=t["confederation"],
                flag_emoji=t["flag_emoji"],
                stats=t["stats"]
            ) for t in response.data]
        except Exception as e:
            logger.error(f"Error getting teams in group {letter} from Supabase: {e}. Falling back to JSON.")
            
    _ensure_loaded()
    letter = letter.upper()
    return [t for t in _teams if t.group_letter == letter]


# ---------------------------------------------------------------------------
# Match helpers
# ---------------------------------------------------------------------------

def load_matches(
    stage: Optional[str] = None,
    group: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Match]:
    """Return matches from Supabase database or JSON fallback with optional filters."""
    if supabase is not None:
        try:
            # Build team mapping for converting foreign key IDs back to 3-letter codes
            teams_res = supabase.table("teams").select("id, code").execute()
            team_map = {t["id"]: t["code"] for t in teams_res.data}
            
            query = supabase.table("matches").select("*")
            if stage:
                query = query.eq("stage", stage)
            if group:
                query = query.eq("group_letter", group.upper())
            if status:
                query = query.eq("status", status)
                
            response = query.execute()
            matches = []
            for m in response.data:
                matches.append(Match(
                    id=m["id"],
                    match_number=m["match_number"],
                    stage=m["stage"],
                    group_letter=m["group_letter"],
                    home_team_code=team_map.get(m["home_team_id"], ""),
                    away_team_code=team_map.get(m["away_team_id"], ""),
                    match_date=m["match_date"],
                    venue=m["venue"] or "",
                    city=m["city"] or "",
                    home_score=m["home_score"],
                    away_score=m["away_score"],
                    status=m["status"]
                ))
            return matches
        except Exception as e:
            logger.error(f"Error loading matches from Supabase: {e}. Falling back to JSON.")

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
    """Find a match by its ID / match_number from Supabase or JSON."""
    if supabase is not None:
        try:
            # Check by internal database ID first
            response = supabase.table("matches").select("*").eq("id", match_id).execute()
            if not response.data:
                # Fallback to checking by match_number (sequential identifier)
                response = supabase.table("matches").select("*").eq("match_number", match_id).execute()
                
            if response.data:
                m = response.data[0]
                teams_res = supabase.table("teams").select("id, code").execute()
                team_map = {t["id"]: t["code"] for t in teams_res.data}
                return Match(
                    id=m["id"],
                    match_number=m["match_number"],
                    stage=m["stage"],
                    group_letter=m["group_letter"],
                    home_team_code=team_map.get(m["home_team_id"], ""),
                    away_team_code=team_map.get(m["away_team_id"], ""),
                    match_date=m["match_date"],
                    venue=m["venue"] or "",
                    city=m["city"] or "",
                    home_score=m["home_score"],
                    away_score=m["away_score"],
                    status=m["status"]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting match {match_id} from Supabase: {e}. Falling back to JSON.")

    _ensure_loaded()
    for m in _matches:
        if m.id == match_id or m.match_number == match_id:
            return m
    return None


def get_upcoming_matches(limit: int = 5) -> list[Match]:
    """Return the next N upcoming matches sorted by date."""
    if supabase is not None:
        try:
            now = datetime.now(timezone.utc).isoformat()
            response = supabase.table("matches")\
                .select("*")\
                .eq("status", "scheduled")\
                .gte("match_date", now)\
                .order("match_date")\
                .limit(limit)\
                .execute()
                
            teams_res = supabase.table("teams").select("id, code").execute()
            team_map = {t["id"]: t["code"] for t in teams_res.data}
            
            return [Match(
                id=m["id"],
                match_number=m["match_number"],
                stage=m["stage"],
                group_letter=m["group_letter"],
                home_team_code=team_map.get(m["home_team_id"], ""),
                away_team_code=team_map.get(m["away_team_id"], ""),
                match_date=m["match_date"],
                venue=m["venue"] or "",
                city=m["city"] or "",
                home_score=m["home_score"],
                away_score=m["away_score"],
                status=m["status"]
            ) for m in response.data]
        except Exception as e:
            logger.error(f"Error getting upcoming matches from Supabase: {e}. Falling back to JSON.")

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
    home = get_team_by_code(match.home_team_code)
    away = get_team_by_code(match.away_team_code)
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
    """Set the result for a match in the database and mark it completed."""
    if supabase is not None:
        try:
            match = get_match_by_id(match_id)
            if match is None:
                return None
                
            # Update score and status in database
            supabase.table("matches").update({
                "home_score": home_score,
                "away_score": away_score,
                "status": "completed",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", match.id).execute()
            
            # Recalculate user prediction points for this match
            _recalculate_prediction_points(match.id, home_score, away_score)
            
            return get_match_by_id(match_id)
        except Exception as e:
            logger.error(f"Error updating match result {match_id} in Supabase: {e}. Falling back to in-memory.")

    _ensure_loaded()
    match = get_match_by_id(match_id)
    if match is None:
        return None
    match.home_score = home_score
    match.away_score = away_score
    match.status = MatchStatus.COMPLETED
    _recalculate_prediction_points_fallback(match)
    return match


# ---------------------------------------------------------------------------
# Prediction helpers (Supabase table)
# ---------------------------------------------------------------------------

def save_prediction(data: MyPredictionCreate) -> MyPrediction:
    """Create or update a user prediction in Supabase."""
    if supabase is not None:
        try:
            # Check if prediction already exists for this match
            response = supabase.table("my_predictions").select("*").eq("match_id", data.match_id).execute()
            
            db_data = {
                "match_id": data.match_id,
                "predicted_home_score": data.predicted_home_score,
                "predicted_away_score": data.predicted_away_score,
                "confidence": int(data.confidence * 100),
                "notes": data.notes,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Calculate points if match is already played
            match = get_match_by_id(data.match_id)
            if match and match.home_score is not None and match.away_score is not None:
                db_data["points_earned"] = _calculate_points(
                    data.predicted_home_score,
                    data.predicted_away_score,
                    match.home_score,
                    match.away_score
                )
                
            if response.data:
                # Update
                res = supabase.table("my_predictions").update(db_data).eq("match_id", data.match_id).execute()
            else:
                # Insert
                res = supabase.table("my_predictions").insert(db_data).execute()
                
            p = res.data[0]
            return MyPrediction(
                id=p["id"],
                match_id=p["match_id"],
                predicted_home_score=p["predicted_home_score"],
                predicted_away_score=p["predicted_away_score"],
                confidence=p["confidence"] / 100.0,
                notes=p["notes"],
                points_earned=p["points_earned"],
                created_at=p["created_at"]
            )
        except Exception as e:
            logger.error(f"Error saving prediction to Supabase: {e}. Falling back to in-memory.")

    # Fallback in-memory
    global _next_prediction_id, _predictions
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
    """Return all user predictions from Supabase (or in-memory fallback)."""
    if supabase is not None:
        try:
            response = supabase.table("my_predictions").select("*").execute()
            return [MyPrediction(
                id=p["id"],
                match_id=p["match_id"],
                predicted_home_score=p["predicted_home_score"],
                predicted_away_score=p["predicted_away_score"],
                confidence=p["confidence"] / 100.0,
                notes=p["notes"],
                points_earned=p["points_earned"],
                created_at=p["created_at"]
            ) for p in response.data]
        except Exception as e:
            logger.error(f"Error getting predictions from Supabase: {e}. Falling back to in-memory.")
            
    return list(_predictions)


def get_prediction_by_match(match_id: int) -> Optional[MyPrediction]:
    """Return user prediction for a specific match."""
    if supabase is not None:
        try:
            response = supabase.table("my_predictions").select("*").eq("match_id", match_id).execute()
            if response.data:
                p = response.data[0]
                return MyPrediction(
                    id=p["id"],
                    match_id=p["match_id"],
                    predicted_home_score=p["predicted_home_score"],
                    predicted_away_score=p["predicted_away_score"],
                    confidence=p["confidence"] / 100.0,
                    notes=p["notes"],
                    points_earned=p["points_earned"],
                    created_at=p["created_at"]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting prediction for match {match_id} from Supabase: {e}. Falling back to in-memory.")

    return next((p for p in _predictions if p.match_id == match_id), None)


def _recalculate_prediction_points(match_id: int, home_score: int, away_score: int) -> None:
    """Recalculate points earned for a prediction in the database."""
    pred = get_prediction_by_match(match_id)
    if pred:
        points = _calculate_points(
            pred.predicted_home_score,
            pred.predicted_away_score,
            home_score,
            away_score
        )
        try:
            supabase.table("my_predictions").update({
                "points_earned": points,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("match_id", match_id).execute()
        except Exception as e:
            logger.error(f"Error updating prediction points in Supabase: {e}")


def _recalculate_prediction_points_fallback(match: Match) -> None:
    """In-memory fallback for recalculating points."""
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


# ---------------------------------------------------------------------------
# AI predictions database cache helpers
# ---------------------------------------------------------------------------

def get_ai_prediction(match_id: int) -> Optional[AIPrediction]:
    """Retrieve AI prediction from database cache if it exists."""
    if supabase is not None:
        try:
            response = supabase.table("ai_predictions").select("*").eq("match_id", match_id).execute()
            if response.data:
                p = response.data[0]
                
                # Check for float normalization (if stored as 0-100 in db or 0-1)
                conf = p["confidence_score"]
                if conf > 1.0:
                    conf = conf / 100.0
                    
                return AIPrediction(
                    match_id=p["match_id"],
                    model_used=p["model_used"] or "gemini-1.5-flash",
                    predicted_home_score=p["predicted_home_score"],
                    predicted_away_score=p["predicted_away_score"],
                    home_win_prob=float(p["home_win_prob"]),
                    draw_prob=float(p["draw_prob"]),
                    away_win_prob=float(p["away_win_prob"]),
                    confidence_score=float(conf),
                    analysis_text=p["analysis_text"] or "",
                    factors=p["factors"] or []
                )
        except Exception as e:
            logger.error(f"Error getting AI prediction cache from Supabase: {e}")
    return None


def save_ai_prediction(pred: AIPrediction) -> None:
    """Save/cache an AI prediction to the database."""
    if supabase is not None:
        try:
            db_data = {
                "match_id": pred.match_id,
                "model_used": pred.model_used,
                "predicted_home_score": pred.predicted_home_score,
                "predicted_away_score": pred.predicted_away_score,
                "home_win_prob": float(pred.home_win_prob),
                "draw_prob": float(pred.draw_prob),
                "away_win_prob": float(pred.away_win_prob),
                "confidence_score": int(pred.confidence_score * 100),
                "analysis_text": pred.analysis_text,
                "factors": pred.factors
            }
            # Check if cache entry exists
            response = supabase.table("ai_predictions").select("id").eq("match_id", pred.match_id).execute()
            if response.data:
                supabase.table("ai_predictions").update(db_data).eq("match_id", pred.match_id).execute()
            else:
                supabase.table("ai_predictions").insert(db_data).execute()
        except Exception as e:
            logger.error(f"Error caching AI prediction in Supabase: {e}")
