from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AnimationStyle = Literal["fade", "zoom", "slide", "typewriter", "pulse"]


class GraphicRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=48, examples=["FIFA"])
    duration: float = Field(4.0, ge=0.5, le=30.0, description="Seconds on screen")
    style: AnimationStyle = Field(
        "pulse",
        description="Always pulse (other values are accepted but ignored)",
    )


class GraphicPushResponse(BaseModel):
    ok: bool = True
    text: str
    style: AnimationStyle
    duration: float
    message: str


class GraphicActiveResponse(BaseModel):
    active: bool
    text: str | None = None
    style: AnimationStyle | None = None
    duration: float | None = None
    remaining: float | None = None
