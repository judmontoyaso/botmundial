"""Router for team-related endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models.team import TeamResponse
from app.services import data_service

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=TeamResponse)
async def list_teams():
    teams = data_service.load_teams()
    return TeamResponse(data=teams, count=len(teams))


@router.get("/group/{letter}", response_model=TeamResponse)
async def get_teams_by_group(letter: str):
    letter = letter.upper()
    if letter not in "ABCDEFGHIJKL" or len(letter) != 1:
        raise HTTPException(status_code=400, detail="Invalid group letter. Must be A-L.")
    teams = data_service.get_teams_by_group(letter)
    if not teams:
        raise HTTPException(status_code=404, detail=f"No teams found for group {letter}")
    return TeamResponse(data=teams, count=len(teams))


@router.get("/{code}", response_model=TeamResponse)
async def get_team_by_code(code: str):
    team = data_service.get_team_by_code(code.upper())
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team '{code.upper()}' not found")
    return TeamResponse(data=team, count=1)


# ---------------------------------------------------------------------------
# Player absences
# ---------------------------------------------------------------------------

class AbsenceCreate(BaseModel):
    player_name: str
    position: Optional[str] = None
    importance: int = 2
    reason: str = "injury"


@router.get("/{code}/absences")
async def get_team_absences(code: str):
    """Get all active player absences for a team."""
    team = data_service.get_team_by_code(code.upper())
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team '{code.upper()}' not found")
    absences = data_service.get_active_absences(code.upper())
    return {"success": True, "data": absences, "count": len(absences)}


@router.post("/{code}/absences", status_code=201)
async def add_team_absence(code: str, body: AbsenceCreate):
    """Add a player absence for a team."""
    team = data_service.get_team_by_code(code.upper())
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team '{code.upper()}' not found")
    absence = data_service.add_player_absence(
        team_code=code.upper(),
        player_name=body.player_name,
        position=body.position,
        importance=body.importance,
        reason=body.reason,
    )
    return {"success": True, "data": absence}


@router.delete("/absences/{absence_id}", status_code=204)
async def delete_absence(absence_id: int):
    """Delete a player absence record."""
    deleted = data_service.delete_player_absence(absence_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Absence {absence_id} not found")
