"""Frame compositor — scorebug, LIVE badge, lower third, animated titles."""

from __future__ import annotations

import math
import time

import cv2
import numpy as np

from app.core import config
from app.services.graphics_store import ActiveGraphic, graphics_store
from app.services.match_store import match_store

_MATCH_CLOCK_START = time.time()


def match_clock() -> str:
    elapsed = int(time.time() - _MATCH_CLOCK_START)
    minutes, seconds = divmod(elapsed % (90 * 60), 60)
    return f"{minutes:02d}:{seconds:02d}"


def draw_rounded_rect(
    frame: np.ndarray,
    pt1: tuple[int, int],
    pt2: tuple[int, int],
    color: tuple[int, int, int],
    alpha: float = 0.75,
) -> None:
    overlay = frame.copy()
    cv2.rectangle(overlay, pt1, pt2, color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def _animation_progress(graphic: ActiveGraphic) -> tuple[float, float, float]:
    """Returns (progress 0..1, appear 0..1, opacity 0..1)."""
    elapsed = time.time() - graphic.started_at
    progress = max(0.0, min(1.0, elapsed / graphic.duration))
    fade_out_start = 0.8
    if progress < 0.15:
        appear = _ease_out_cubic(progress / 0.15)
    else:
        appear = 1.0
    if progress >= fade_out_start:
        opacity = max(0.0, 1.0 - (progress - fade_out_start) / (1.0 - fade_out_start))
    else:
        opacity = appear
    return progress, appear, opacity


def draw_center_text(
    frame: np.ndarray,
    text: str,
    scale: float,
    opacity: float,
    offset_x: int = 0,
    offset_y: int = 0,
) -> None:
    """Draw center title with no background plate — text only."""
    if opacity <= 0.01 or not text:
        return

    h, w = frame.shape[:2]
    thickness = max(2, int(scale * 2.8))
    font = cv2.FONT_HERSHEY_DUPLEX
    (tw, th), _baseline = cv2.getTextSize(text, font, scale, thickness)
    x = int((w - tw) / 2) + offset_x
    y = int((h + th) / 2) + offset_y

    overlay = frame.copy()
    # Soft shadow / outline only — no filled background box
    cv2.putText(
        overlay,
        text,
        (x + 2, y + 2),
        font,
        scale,
        (0, 0, 0),
        thickness + 4,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        text,
        (x, y),
        font,
        scale,
        (0, 0, 0),
        thickness + 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        text,
        (x, y),
        font,
        scale,
        (40, 215, 255),
        thickness,
        cv2.LINE_AA,
    )
    cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)


def burn_in_animated_title(frame: np.ndarray, graphic: ActiveGraphic) -> None:
    """Always pulse — scale + opacity breathe with a soft entrance/exit."""
    progress, appear, fade_opacity = _animation_progress(graphic)
    text = graphic.text
    base_scale = 2.6 if len(text) <= 8 else 1.7

    # Smooth pulse (two beats over the visible hold)
    breath = 0.5 + 0.5 * math.sin(progress * math.pi * 4)
    scale = base_scale * (0.88 + 0.22 * breath) * (0.75 + 0.25 * appear)
    opacity = fade_opacity * (0.75 + 0.25 * breath)

    draw_center_text(frame, text, scale, opacity)


def burn_in_chrome(frame: np.ndarray) -> None:
    """Permanent IBC chrome: live scorebug + LIVE badge."""
    w = frame.shape[1]
    match = match_store.get()

    draw_rounded_rect(frame, (20, 20), (420, 90), (20, 20, 20), alpha=0.8)
    cv2.putText(
        frame,
        f"{match.home_team} {match.home_score}  -  {match.away_score} {match.away_team}",
        (35, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"{match_clock()}  |  LIVE",
        (35, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (80, 220, 120),
        1,
        cv2.LINE_AA,
    )

    draw_rounded_rect(frame, (w - 140, 20), (w - 20, 60), (0, 0, 200), alpha=0.85)
    cv2.putText(
        frame,
        "LIVE",
        (w - 115, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def compose_frame(frame: np.ndarray) -> np.ndarray:
    """IBC graphics pass: chrome + optional animated center title."""
    burn_in_chrome(frame)
    graphic = graphics_store.get()
    if graphic is not None:
        burn_in_animated_title(frame, graphic)
    return frame


def no_signal_frame() -> np.ndarray:
    frame = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), dtype=np.uint8)
    cv2.putText(
        frame,
        "NO CAMERA SIGNAL",
        (360, 360),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 0, 255),
        3,
        cv2.LINE_AA,
    )
    return frame
