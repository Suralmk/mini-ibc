from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

AnimationStyle = Literal["fade", "zoom", "slide", "typewriter", "pulse"]
GraphicKind = Literal["title", "lower_third", "stats"]


class GraphicRequest(BaseModel):
    kind: GraphicKind = Field("title", description="Overlay type on the world feed")
    duration: float = Field(5.0, ge=0.5, le=30.0, description="Seconds on screen")

    # title (pulse)
    text: str | None = Field(None, max_length=48, examples=["FIFA"])
    style: AnimationStyle = Field("pulse")

    # lower_third
    title: str | None = Field(None, max_length=48)
    subtitle: str | None = Field(None, max_length=64)
    line3: str | None = Field(None, max_length=64)

    # stats
    home_possession: int | None = Field(None, ge=0, le=100)
    away_possession: int | None = Field(None, ge=0, le=100)
    home_shots: int | None = Field(None, ge=0, le=99)
    away_shots: int | None = Field(None, ge=0, le=99)
    home_on_target: int | None = Field(None, ge=0, le=99)
    away_on_target: int | None = Field(None, ge=0, le=99)
    home_label: str | None = Field(None, max_length=16)
    away_label: str | None = Field(None, max_length=16)
    data_source: str = Field(
        "Opta / Stats Perform / FIFA",
        max_length=64,
        description="Simulated data-feed badge",
    )

    @model_validator(mode="after")
    def validate_kind_fields(self) -> GraphicRequest:
        if self.kind == "title":
            if not (self.text and self.text.strip()):
                raise ValueError("text is required for title graphics")
        elif self.kind == "lower_third":
            if not (self.title and self.title.strip()):
                raise ValueError("title is required for lower_third")
        elif self.kind == "stats":
            hp = 50 if self.home_possession is None else self.home_possession
            ap = 50 if self.away_possession is None else self.away_possession
            if hp + ap != 100:
                # auto-balance away if only home set, else normalize
                if self.away_possession is None:
                    self.away_possession = 100 - hp
                elif self.home_possession is None:
                    self.home_possession = 100 - ap
                else:
                    total = hp + ap
                    if total <= 0:
                        self.home_possession, self.away_possession = 50, 50
                    else:
                        self.home_possession = round(100 * hp / total)
                        self.away_possession = 100 - self.home_possession
            if self.home_shots is None:
                self.home_shots = 0
            if self.away_shots is None:
                self.away_shots = 0
            if self.home_on_target is None:
                self.home_on_target = min(self.home_shots, max(0, self.home_shots - 2))
            if self.away_on_target is None:
                self.away_on_target = min(self.away_shots, max(0, self.away_shots // 2))
            self.home_on_target = min(self.home_on_target, self.home_shots)
            self.away_on_target = min(self.away_on_target, self.away_shots)
        return self


class GraphicPushResponse(BaseModel):
    ok: bool = True
    kind: GraphicKind
    text: str | None = None
    title: str | None = None
    style: AnimationStyle | None = None
    duration: float
    message: str


class GraphicActiveResponse(BaseModel):
    active: bool
    kind: GraphicKind | None = None
    text: str | None = None
    title: str | None = None
    subtitle: str | None = None
    style: AnimationStyle | None = None
    duration: float | None = None
    remaining: float | None = None
