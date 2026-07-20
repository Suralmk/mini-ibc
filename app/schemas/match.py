from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Period = Literal["1H", "HT", "2H", "ET", "FT"]


class MatchStateResponse(BaseModel):
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    score: str
    period: Period
    clock_minute: int
    stoppage: int
    clock: str


class MatchUpdateRequest(BaseModel):
    home_team: str | None = Field(None, max_length=12)
    away_team: str | None = Field(None, max_length=12)
    home_score: int | None = Field(None, ge=0, le=99)
    away_score: int | None = Field(None, ge=0, le=99)
    period: Period | None = None
    clock_minute: int | None = Field(None, ge=0, le=120)
    stoppage: int | None = Field(None, ge=0, le=20)


class GoalRequest(BaseModel):
    side: Literal["home", "away"]
    announce: bool = Field(
        True,
        description="Also push a GOAL title graphic onto the world feed",
    )
