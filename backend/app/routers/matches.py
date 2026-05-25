"""Router for match-related endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.match import MatchResponse, MatchResult
from app.services import data_service

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/upcoming", response_model=MatchResponse)
async def get_upcoming_matches(limit: int = Query(default=5, ge=1, le=20)):
    """Return the next N upcoming scheduled matches."""
    matches = data_service.get_upcoming_matches(limit)
    enriched = [data_service.enrich_match(m) for m in matches]
    return MatchResponse(data=enriched, count=len(enriched))


@router.get("", response_model=MatchResponse)
async def list_matches(
    stage: Optional[str] = Query(default=None, description="Filter by stage (e.g. group)"),
    group: Optional[str] = Query(default=None, description="Filter by group letter"),
    status: Optional[str] = Query(default=None, description="Filter by status (scheduled, completed)"),
):
    """List all matches with optional filters."""
    matches = data_service.load_matches(stage=stage, group=group, status=status)
    enriched = [data_service.enrich_match(m) for m in matches]
    return MatchResponse(data=enriched, count=len(enriched))


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: int):
    """Get a single match by its ID / match_number."""
    match = data_service.get_match_by_id(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    enriched = data_service.enrich_match(match)
    return MatchResponse(data=enriched, count=1)


@router.put("/{match_id}/result", response_model=MatchResponse)
async def update_match_result(match_id: int, result: MatchResult):
    """Set the final score for a match (marks it completed)."""
    match = data_service.update_match_result(match_id, result.home_score, result.away_score)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    enriched = data_service.enrich_match(match)
    return MatchResponse(data=enriched, count=1)
