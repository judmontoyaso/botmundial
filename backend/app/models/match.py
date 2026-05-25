"""Pydantic models for matches and results."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    """Possible match statuses."""

    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    POSTPONED = "postponed"


class MatchStage(str, Enum):
    """Tournament stages."""

    GROUP = "group"
    ROUND_OF_32 = "round_of_32"
    ROUND_OF_16 = "round_of_16"
    QUARTERFINAL = "quarterfinal"
    SEMIFINAL = "semifinal"
    THIRD_PLACE = "third_place"
    FINAL = "final"


class Match(BaseModel):
    """A single match in the tournament."""

    id: int | None = Field(default=None, description="Unique match ID")
    match_number: int = Field(..., ge=1, description="Sequential match number")
    stage: MatchStage = Field(..., description="Tournament stage")
    group_letter: str | None = Field(default=None, description="Group letter (group stage only)")
    home_team_code: str = Field(..., min_length=3, max_length=3)
    away_team_code: str = Field(..., min_length=3, max_length=3)
    match_date: datetime = Field(..., description="Match date and kickoff time (UTC)")
    venue: str = Field(..., description="Stadium name")
    city: str = Field(..., description="Host city")
    home_score: int | None = Field(default=None, ge=0, description="Home team goals")
    away_score: int | None = Field(default=None, ge=0, description="Away team goals")
    status: MatchStatus = Field(default=MatchStatus.SCHEDULED)


class MatchWithTeams(BaseModel):
    """Match enriched with full team info for display."""

    match: Match
    home_team_name: str
    away_team_name: str
    home_team_flag: str
    away_team_flag: str
    home_team_ranking: int
    away_team_ranking: int


class MatchResult(BaseModel):
    """Payload for updating a match result."""

    home_score: int = Field(..., ge=0, description="Home team final score")
    away_score: int = Field(..., ge=0, description="Away team final score")


class MatchResponse(BaseModel):
    """API response wrapper for match data."""

    success: bool = True
    data: Match | MatchWithTeams | list[Match] | list[MatchWithTeams]
    count: int = 1
