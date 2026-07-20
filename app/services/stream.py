"""Shared camera frame fan-out for WebSocket (and optional MJPEG) clients."""

from __future__ import annotations

import threading
import time

import cv2

from app.core import config
from app.services.camera import open_camera
from app.services.compositor import compose_frame, no_signal_frame


class FrameHub:
    """One camera capture thread; many subscribers wait on new JPEG frames."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._jpeg: bytes | None = None
        self._seq = 0
        self._started = False

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
            threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self) -> None:
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY]
        cap = None
        try:
            cap = open_camera()
            while True:
                ok, frame = cap.read()
                if not ok:
                    frame = no_signal_frame()
                else:
                    frame = compose_frame(frame)

                ok, buffer = cv2.imencode(".jpg", frame, encode_params)
                if not ok:
                    time.sleep(0.01)
                    continue

                with self._cond:
                    self._jpeg = buffer.tobytes()
                    self._seq += 1
                    self._cond.notify_all()
        except Exception:
            placeholder = no_signal_frame()
            ok, buffer = cv2.imencode(".jpg", placeholder, encode_params)
            if ok:
                with self._cond:
                    self._jpeg = buffer.tobytes()
                    self._seq += 1
                    self._cond.notify_all()
            time.sleep(1.0)
        finally:
            if cap is not None:
                cap.release()
            with self._lock:
                self._started = False

    def wait_next_jpeg(self, last_seq: int) -> tuple[int, bytes]:
        """Block until a newer frame than last_seq is available."""
        self.start()
        with self._cond:
            while True:
                while self._seq == last_seq or self._jpeg is None:
                    self._cond.wait(timeout=1.0)
                    if not self._started:
                        self.start()
                assert self._jpeg is not None
                return self._seq, self._jpeg


frame_hub = FrameHub()
