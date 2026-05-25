"""Pydantic models for teams and group standings."""

from pydantic import BaseModel, Field


class TeamStats(BaseModel):
    """Statistical data for a team."""

    goals_scored_avg: float = Field(..., description="Average goals scored per match")
    goals_conceded_avg: float = Field(..., description="Average goals conceded per match")
    wins_last_10: int = Field(..., ge=0, le=10, description="Wins in last 10 matches")
    draws_last_10: int = Field(..., ge=0, le=10, description="Draws in last 10 matches")
    losses_last_10: int = Field(..., ge=0, le=10, description="Losses in last 10 matches")
    world_cup_appearances: int = Field(..., ge=0, description="Total World Cup appearances")
    best_finish: str = Field(..., description="Best World Cup finish")


class Team(BaseModel):
    """A national team participating in the World Cup."""

    id: int | None = Field(default=None, description="Unique team ID")
    name: str = Field(..., description="Full team name")
    code: str = Field(..., min_length=3, max_length=3, description="3-letter FIFA code")
    group_letter: str = Field(..., min_length=1, max_length=1, description="Group letter A-L")
    fifa_ranking: int = Field(..., ge=1, description="Current FIFA ranking")
    confederation: str = Field(..., description="FIFA confederation (e.g. UEFA, CONMEBOL)")
    flag_emoji: str = Field(..., description="Country flag emoji")
    stats: TeamStats = Field(..., description="Team statistics")


class TeamResponse(BaseModel):
    """API response wrapper for team data."""

    success: bool = True
    data: Team | list[Team]
    count: int = 1


class GroupStanding(BaseModel):
    """A team's standing within its group."""

    team_code: str
    team_name: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    position: int = 0
