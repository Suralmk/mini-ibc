"""Frame compositor — scorebug, LIVE badge, titles, lower thirds, stats."""

from __future__ import annotations

import math

import cv2
import numpy as np

from app.core import config
from app.services.graphics_store import ActiveGraphic, graphics_store
from app.services.match_store import match_store


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
    import time

    elapsed = time.time() - graphic.started_at
    progress = max(0.0, min(1.0, elapsed / graphic.duration))
    fade_out_start = 0.82
    if progress < 0.12:
        appear = _ease_out_cubic(progress / 0.12)
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
    cv2.putText(
        overlay, text, (x + 2, y + 2), font, scale, (0, 0, 0), thickness + 4, cv2.LINE_AA
    )
    cv2.putText(
        overlay, text, (x, y), font, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA
    )
    cv2.putText(
        overlay, text, (x, y), font, scale, (40, 215, 255), thickness, cv2.LINE_AA
    )
    cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)


def burn_in_animated_title(frame: np.ndarray, graphic: ActiveGraphic) -> None:
    """Pulse title — scale + opacity breathe with soft entrance/exit."""
    progress, appear, fade_opacity = _animation_progress(graphic)
    text = graphic.text
    base_scale = 2.6 if len(text) <= 8 else 1.7
    breath = 0.5 + 0.5 * math.sin(progress * math.pi * 4)
    scale = base_scale * (0.88 + 0.22 * breath) * (0.75 + 0.25 * appear)
    opacity = fade_opacity * (0.75 + 0.25 * breath)
    draw_center_text(frame, text, scale, opacity)


def burn_in_scorebug(frame: np.ndarray) -> None:
    """FIFA-style scorebug (top-left) + LIVE pill (top-right)."""
    h, w = frame.shape[:2]
    match = match_store.get()

    home = match.home_team[:3]
    away = match.away_team[:3]
    clock = match.clock_display()
    font = cv2.FONT_HERSHEY_SIMPLEX
    mint = (188, 255, 168)

    flag_w, flag_h = 22, 14
    score_box = 36
    pad_x = 14
    gap = 8

    (home_w, _), _ = cv2.getTextSize(home, font, 0.7, 2)
    (away_w, _), _ = cv2.getTextSize(away, font, 0.7, 2)
    (hs_w, _), _ = cv2.getTextSize(str(match.home_score), font, 0.9, 2)
    (as_w, _), _ = cv2.getTextSize(str(match.away_score), font, 0.9, 2)
    (clk_w, _), _ = cv2.getTextSize(clock, font, 0.62, 2)

    # Layout widths
    home_block = flag_w + 8 + home_w
    away_block = away_w + 8 + flag_w
    scores_block = score_box + 6 + score_box
    clock_block = clk_w + 16
    strip_w = (
        pad_x
        + home_block
        + gap
        + scores_block
        + gap
        + away_block
        + 12
        + 2
        + 12
        + clock_block
        + pad_x
    )
    strip_h = 52
    x0, y0 = 24, 20
    x1, y1 = x0 + strip_w, y0 + strip_h
    radius = 12

    layer = frame.copy()
    _fill_round_rect(layer, (x0, y0), (x1, y1), (28, 28, 32), radius)

    cy = y0 + 34  # text baseline
    cx = x0 + pad_x

    # Home flag + code
    _draw_mini_flag(layer, home, cx, cy - 12, flag_w, flag_h)
    cx += flag_w + 8
    cv2.putText(layer, home, (cx, cy), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cx += home_w + gap

    # Home score box
    sx1, sy1 = cx, y0 + 8
    sx2, sy2 = cx + score_box, y0 + strip_h - 8
    _fill_round_rect(layer, (sx1, sy1), (sx2, sy2), (45, 48, 55), 6)
    cv2.putText(
        layer,
        str(match.home_score),
        (sx1 + (score_box - hs_w) // 2, cy + 1),
        font,
        0.9,
        mint,
        2,
        cv2.LINE_AA,
    )
    cx = sx2 + 6

    # Away score box
    sx1, sy1 = cx, y0 + 8
    sx2, sy2 = cx + score_box, y0 + strip_h - 8
    _fill_round_rect(layer, (sx1, sy1), (sx2, sy2), (45, 48, 55), 6)
    cv2.putText(
        layer,
        str(match.away_score),
        (sx1 + (score_box - as_w) // 2, cy + 1),
        font,
        0.9,
        mint,
        2,
        cv2.LINE_AA,
    )
    cx = sx2 + gap

    # Away code + flag
    cv2.putText(layer, away, (cx, cy), font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cx += away_w + 8
    _draw_mini_flag(layer, away, cx, cy - 12, flag_w, flag_h)
    cx += flag_w + 12

    # Vertical divider
    cv2.line(layer, (cx, y0 + 12), (cx, y1 - 12), (200, 200, 210), 1, cv2.LINE_AA)
    cx += 12

    # Clock only (no period / ET label)
    cv2.putText(layer, clock, (cx, cy + 1), font, 0.62, mint, 2, cv2.LINE_AA)

    _draw_gradient_border(layer, (x0, y0), (x1, y1), thickness=3, radius=radius)
    cv2.addWeighted(layer, 0.96, frame, 0.04, 0, frame)

    # LIVE pill top-right (same family)
    live_w, live_h = 82, 32
    lx0, ly0 = w - live_w - 24, 20
    lx1, ly1 = lx0 + live_w, ly0 + live_h
    live = frame.copy()
    _fill_round_rect(live, (lx0, ly0), (lx1, ly1), (40, 40, 200), 10)
    cv2.circle(live, (lx0 + 16, ly0 + live_h // 2), 5, (220, 220, 255), -1, cv2.LINE_AA)
    cv2.putText(
        live, "LIVE", (lx0 + 28, ly0 + 22), font, 0.55, (255, 255, 255), 2, cv2.LINE_AA
    )
    _draw_gradient_border(live, (lx0, ly0), (lx1, ly1), thickness=2, radius=10)
    cv2.addWeighted(live, 0.95, frame, 0.05, 0, frame)


def burn_in_lower_third(frame: np.ndarray, graphic: ActiveGraphic) -> None:
    """FIFA-style lower third — slides up from bottom."""
    _, appear, opacity = _animation_progress(graphic)
    if opacity <= 0.01:
        return

    h, w = frame.shape[:2]
    # Slide up from below the frame
    slide = int((1.0 - appear) * 110)

    has_line3 = bool(graphic.line3.strip())
    bar_h = 92 if has_line3 else 76
    bar_w = min(720, w - 80)
    x1 = 40
    x2 = x1 + bar_w
    y2 = h - 36 + slide
    y1 = y2 - bar_h
    radius = 14
    header_h = 8
    mint = (188, 255, 168)
    hdr_color = (200, 95, 55)  # blue accent (BGR)

    layer = frame.copy()
    _fill_round_rect(layer, (x1, y1), (x2, y2), (28, 28, 32), radius)

    # Top accent strip (same family as MATCH STATS header)
    cv2.rectangle(layer, (x1 + radius, y1), (x2 - radius, y1 + header_h + 4), hdr_color, -1)
    cv2.rectangle(layer, (x1, y1 + 4), (x2, y1 + header_h + 2), hdr_color, -1)
    # Left accent bar
    cv2.rectangle(layer, (x1, y1 + header_h), (x1 + 6, y2), hdr_color, -1)

    font = cv2.FONT_HERSHEY_SIMPLEX
    title = graphic.title
    subtitle = graphic.subtitle
    line3 = graphic.line3

    text_x = x1 + 24
    cv2.putText(
        layer, title, (text_x, y1 + 38), font, 0.85, (255, 255, 255), 2, cv2.LINE_AA
    )
    if subtitle:
        cv2.putText(
            layer,
            subtitle,
            (text_x, y1 + 62),
            font,
            0.55,
            mint,
            1,
            cv2.LINE_AA,
        )
    if has_line3:
        cv2.putText(
            layer,
            line3,
            (text_x, y1 + 82),
            font,
            0.48,
            (210, 215, 225),
            1,
            cv2.LINE_AA,
        )

    _draw_gradient_border(layer, (x1, y1), (x2, y2), thickness=3, radius=radius)
    cv2.addWeighted(layer, opacity * 0.97, frame, 1 - opacity * 0.97, 0, frame)


def _rounded_rect_points(
    x1: int, y1: int, x2: int, y2: int, r: int, segments: int = 16
) -> np.ndarray:
    """Clockwise contour of a rounded rectangle (smooth continuous corners)."""
    r = max(1, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    pts: list[list[int]] = []

    def arc(cx: float, cy: float, a0: float, a1: float) -> None:
        for i in range(segments + 1):
            a = a0 + (a1 - a0) * (i / segments)
            pts.append(
                [int(round(cx + r * np.cos(a))), int(round(cy + r * np.sin(a)))]
            )

    arc(x1 + r, y1 + r, np.pi, 1.5 * np.pi)        # top-left
    arc(x2 - r, y1 + r, 1.5 * np.pi, 2.0 * np.pi)  # top-right
    arc(x2 - r, y2 - r, 0.0, 0.5 * np.pi)          # bottom-right
    arc(x1 + r, y2 - r, 0.5 * np.pi, np.pi)        # bottom-left
    return np.asarray(pts, dtype=np.int32)


def _fill_round_rect(
    img: np.ndarray,
    pt1: tuple[int, int],
    pt2: tuple[int, int],
    color: tuple[int, int, int],
    radius: int = 12,
) -> None:
    x1, y1 = pt1
    x2, y2 = pt2
    if x2 <= x1 or y2 <= y1:
        return
    r = max(1, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    pts = _rounded_rect_points(x1, y1, x2, y2, r)
    cv2.fillPoly(img, [pts], color, cv2.LINE_AA)


# Border stops (BGR) — gradient of the design's own accent colors:
# header blue accent → mint green (scores) → header blue accent.
_BORDER_STOPS = (0.0, 0.5, 1.0)
_BORDER_COLORS = np.array(
    [
        (200, 95, 55),    # blue header accent
        (188, 255, 168),  # mint green
        (200, 95, 55),    # blue header accent
    ],
    dtype=np.float32,
)


def _draw_gradient_border(
    img: np.ndarray,
    pt1: tuple[int, int],
    pt2: tuple[int, int],
    thickness: int = 2,
    radius: int = 14,
) -> None:
    """
    Smooth rounded rainbow border (135° magenta→blue→green→orange), matching
    the editor Scorebug preview. Uses a 2× supersampled outer−inner ring mask
    so corners stay clean — no line/arc joint blobs or pixel stairs.
    """
    x1, y1 = pt1
    x2, y2 = pt2
    if x2 - x1 < 8 or y2 - y1 < 8:
        return

    t = max(1, min(thickness, 3))
    r = max(2, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))

    h, w = img.shape[:2]
    pad = t + 1
    ox1, oy1 = max(0, x1 - pad), max(0, y1 - pad)
    ox2, oy2 = min(w, x2 + pad + 1), min(h, y2 + pad + 1)
    rw, rh = ox2 - ox1, oy2 - oy1
    if rw < 4 or rh < 4:
        return

    scale = 2
    mask = np.zeros((rh * scale, rw * scale), dtype=np.uint8)
    lx1 = (x1 - ox1) * scale
    ly1 = (y1 - oy1) * scale
    lx2 = (x2 - ox1) * scale
    ly2 = (y2 - oy1) * scale
    sr = r * scale
    st = t * scale
    outer = _rounded_rect_points(lx1, ly1, lx2, ly2, sr, segments=24)
    inner = _rounded_rect_points(
        lx1 + st, ly1 + st, lx2 - st, ly2 - st, max(1, sr - st), segments=24
    )
    cv2.fillPoly(mask, [outer], 255)
    cv2.fillPoly(mask, [inner], 0)
    ring = cv2.resize(mask, (rw, rh), interpolation=cv2.INTER_AREA)
    alpha = ring.astype(np.float32) * (1.0 / 255.0)
    if float(alpha.max()) < 1e-3:
        return

    # 135° diagonal gradient: 0 at top-left → 1 at bottom-right
    denom = float((x2 - x1) + (y2 - y1)) or 1.0
    xs = (np.arange(ox1, ox2, dtype=np.float32) - x1).reshape(1, -1)
    ys = (np.arange(oy1, oy2, dtype=np.float32) - y1).reshape(-1, 1)
    tt = np.clip((xs + ys) / denom, 0.0, 1.0)

    grad = np.empty((rh, rw, 3), dtype=np.float32)
    flat = tt.ravel()
    for c in range(3):
        grad[:, :, c] = np.interp(
            flat, _BORDER_STOPS, _BORDER_COLORS[:, c]
        ).reshape(rh, rw)

    a = alpha[:, :, None]
    roi = img[oy1:oy2, ox1:ox2].astype(np.float32)
    roi = roi * (1.0 - a) + grad * a
    img[oy1:oy2, ox1:ox2] = np.clip(roi, 0, 255).astype(np.uint8)


def _lerp_color(
    a: tuple[int, int, int], b: tuple[int, int, int], t: float
) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _draw_mini_flag(img: np.ndarray, code: str, x: int, y: int, fw: int = 22, fh: int = 14) -> None:
    """Tiny flag approximation by team code (BGR)."""
    c = code.upper()[:3]
    if c in ("ESP", "SPA"):
        cv2.rectangle(img, (x, y), (x + fw, y + fh // 3), (40, 40, 200), -1)
        cv2.rectangle(img, (x, y + fh // 3), (x + fw, y + 2 * fh // 3), (0, 200, 240), -1)
        cv2.rectangle(img, (x, y + 2 * fh // 3), (x + fw, y + fh), (40, 40, 200), -1)
    elif c in ("ARG",):
        cv2.rectangle(img, (x, y), (x + fw, y + fh // 3), (220, 180, 100), -1)
        cv2.rectangle(img, (x, y + fh // 3), (x + fw, y + 2 * fh // 3), (255, 255, 255), -1)
        cv2.rectangle(img, (x, y + 2 * fh // 3), (x + fw, y + fh), (220, 180, 100), -1)
        cv2.circle(img, (x + fw // 2, y + fh // 2), 2, (0, 180, 255), -1, cv2.LINE_AA)
    elif c in ("FRA",):
        band = fw // 3
        cv2.rectangle(img, (x, y), (x + band, y + fh), (180, 60, 0), -1)
        cv2.rectangle(img, (x + band, y), (x + 2 * band, y + fh), (255, 255, 255), -1)
        cv2.rectangle(img, (x + 2 * band, y), (x + fw, y + fh), (60, 60, 220), -1)
    else:
        cv2.rectangle(img, (x, y), (x + fw, y + fh), (80, 90, 110), -1)
        cv2.putText(
            img,
            c[:1],
            (x + 6, y + fh - 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    cv2.rectangle(img, (x, y), (x + fw, y + fh), (220, 220, 230), 1)


def burn_in_stats(frame: np.ndarray, graphic: ActiveGraphic) -> None:
    """FIFA-style MATCH STATS card — bottom-left."""
    _, appear, opacity = _animation_progress(graphic)
    if opacity <= 0.01:
        return

    h, w = frame.shape[:2]
    card_w, card_h = 440, 230
    slide = int((1.0 - appear) * 50)
    x1 = 28 - slide
    y2 = h - 28
    y1 = y2 - card_h
    x2 = x1 + card_w
    radius = 16
    header_h = 40

    layer = frame.copy()

    # Body (dark charcoal)
    _fill_round_rect(layer, (x1, y1), (x2, y2), (32, 32, 36), radius)

    # Blue header band
    hdr_color = (200, 95, 55)  # BGR
    cv2.rectangle(layer, (x1, y1 + radius), (x2, y1 + header_h), hdr_color, -1)
    cv2.rectangle(layer, (x1 + radius, y1), (x2 - radius, y1 + radius + 2), hdr_color, -1)
    cv2.circle(layer, (x1 + radius, y1 + radius), radius, hdr_color, -1, cv2.LINE_AA)
    cv2.circle(layer, (x2 - radius, y1 + radius), radius, hdr_color, -1, cv2.LINE_AA)

    font = cv2.FONT_HERSHEY_SIMPLEX
    title = "MATCH STATS"
    (tw, _), _ = cv2.getTextSize(title, font, 0.7, 2)
    cv2.putText(
        layer,
        title,
        (x1 + (card_w - tw) // 2, y1 + 28),
        font,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    home = (graphic.home_label or "HOME")[:3]
    away = (graphic.away_label or "AWAY")[:3]
    mint = (188, 255, 168)
    mid_x = (x1 + x2) // 2

    team_y = y1 + header_h + 32
    _draw_mini_flag(layer, home, x1 + 32, team_y - 12, 24, 15)
    cv2.putText(layer, home, (x1 + 64, team_y + 2), font, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.line(layer, (mid_x, team_y - 16), (mid_x, team_y + 8), (240, 240, 245), 2, cv2.LINE_AA)
    (aw, _), _ = cv2.getTextSize(away, font, 0.75, 2)
    away_text_x = x2 - 32 - 24 - 10 - aw
    cv2.putText(layer, away, (away_text_x, team_y + 2), font, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    _draw_mini_flag(layer, away, x2 - 32 - 24, team_y - 12, 24, 15)

    rows = [
        ("ATTEMPTS AT GOAL", graphic.home_shots, graphic.away_shots),
        ("ATTEMPTS ON TARGET", graphic.home_on_target, graphic.away_on_target),
        ("POSSESSION %", graphic.home_possession, graphic.away_possession),
    ]
    row_y0 = team_y + 38
    for i, (label, lv, rv) in enumerate(rows):
        yy = row_y0 + i * 34
        left, right = str(lv), str(rv)
        (lw, _), _ = cv2.getTextSize(left, font, 0.78, 2)
        (lab_w, _), _ = cv2.getTextSize(label, font, 0.45, 1)
        cv2.putText(layer, left, (mid_x - 100 - lw, yy), font, 0.78, mint, 2, cv2.LINE_AA)
        cv2.putText(
            layer, label, (mid_x - lab_w // 2, yy), font, 0.45, (255, 255, 255), 1, cv2.LINE_AA
        )
        cv2.putText(layer, right, (mid_x + 100, yy), font, 0.78, mint, 2, cv2.LINE_AA)

    _draw_gradient_border(layer, (x1, y1), (x2, y2), thickness=4, radius=radius)

    cv2.addWeighted(layer, opacity * 0.97, frame, 1 - opacity * 0.97, 0, frame)



def compose_frame(frame: np.ndarray) -> np.ndarray:
    """IBC graphics pass: scorebug chrome + optional timed overlay."""
    burn_in_scorebug(frame)
    graphic = graphics_store.get()
    if graphic is None:
        return frame
    if graphic.kind == "title":
        burn_in_animated_title(frame, graphic)
    elif graphic.kind == "lower_third":
        burn_in_lower_third(frame, graphic)
    elif graphic.kind == "stats":
        burn_in_stats(frame, graphic)
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
