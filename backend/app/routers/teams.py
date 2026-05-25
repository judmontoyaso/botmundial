"""Router for team-related endpoints."""

from fastapi import APIRouter, HTTPException

from app.models.team import TeamResponse
from app.services import data_service

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=TeamResponse)
async def list_teams():
    """Return all 48 teams."""
    teams = data_service.load_teams()
    return TeamResponse(data=teams, count=len(teams))


@router.get("/group/{letter}", response_model=TeamResponse)
async def get_teams_by_group(letter: str):
    """Return the four teams in a given group (A-L)."""
    letter = letter.upper()
    if letter not in "ABCDEFGHIJKL" or len(letter) != 1:
        raise HTTPException(status_code=400, detail="Invalid group letter. Must be A-L.")
    teams = data_service.get_teams_by_group(letter)
    if not teams:
        raise HTTPException(status_code=404, detail=f"No teams found for group {letter}")
    return TeamResponse(data=teams, count=len(teams))


@router.get("/{code}", response_model=TeamResponse)
async def get_team_by_code(code: str):
    """Return a single team by its 3-letter FIFA code."""
    team = data_service.get_team_by_code(code.upper())
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team '{code.upper()}' not found")
    return TeamResponse(data=team, count=1)
