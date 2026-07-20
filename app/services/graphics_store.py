from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from app.schemas.graphics import AnimationStyle, GraphicRequest


@dataclass
class ActiveGraphic:
    text: str
    style: AnimationStyle
    duration: float
    started_at: float


class GraphicsStore:
    """Thread-safe in-memory store for the current center-title graphic."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: ActiveGraphic | None = None

    def set(self, req: GraphicRequest) -> ActiveGraphic:
        graphic = ActiveGraphic(
            text=req.text.strip().upper(),
            style="pulse",
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
