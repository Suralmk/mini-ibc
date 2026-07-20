from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from app.schemas.graphics import AnimationStyle, GraphicKind, GraphicRequest


@dataclass
class ActiveGraphic:
    kind: GraphicKind
    duration: float
    started_at: float
    style: AnimationStyle = "pulse"
    text: str = ""
    title: str = ""
    subtitle: str = ""
    line3: str = ""
    home_possession: int = 50
    away_possession: int = 50
    home_shots: int = 0
    away_shots: int = 0
    home_on_target: int = 0
    away_on_target: int = 0
    home_label: str = ""
    away_label: str = ""
    data_source: str = "Opta / Stats Perform / FIFA"


class GraphicsStore:
    """Thread-safe in-memory store for the current timed overlay."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: ActiveGraphic | None = None

    def set(self, req: GraphicRequest) -> ActiveGraphic:
        kind = req.kind
        if kind == "title":
            graphic = ActiveGraphic(
                kind="title",
                text=(req.text or "").strip().upper(),
                style="pulse",
                duration=req.duration,
                started_at=time.time(),
            )
        elif kind == "lower_third":
            graphic = ActiveGraphic(
                kind="lower_third",
                title=(req.title or "").strip(),
                subtitle=(req.subtitle or "").strip(),
                line3=(req.line3 or "").strip(),
                duration=req.duration,
                started_at=time.time(),
            )
        else:
            graphic = ActiveGraphic(
                kind="stats",
                home_possession=req.home_possession or 50,
                away_possession=req.away_possession or 50,
                home_shots=req.home_shots or 0,
                away_shots=req.away_shots or 0,
                home_on_target=req.home_on_target or 0,
                away_on_target=req.away_on_target or 0,
                home_label=(req.home_label or "").strip().upper(),
                away_label=(req.away_label or "").strip().upper(),
                data_source=req.data_source.strip() or "Opta / Stats Perform / FIFA",
                duration=req.duration,
                started_at=time.time(),
            )
        with self._lock:
            self._active = graphic
        return graphic

    def get(self) -> ActiveGraphic | None:
        with self._lock:
            g = self._active
            if g is None:
                return None
            if time.time() - g.started_at > g.duration:
                return None
            return g

    def remaining_seconds(self, graphic: ActiveGraphic) -> float:
        return max(0.0, graphic.duration - (time.time() - graphic.started_at))


graphics_store = GraphicsStore()
