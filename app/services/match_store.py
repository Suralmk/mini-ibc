from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass
from typing import Literal

from app.core import config

Period = Literal["1H", "HT", "2H", "ET", "FT"]


@dataclass
class MatchState:
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    period: Period = "1H"
    clock_minute: int = 0
    stoppage: int = 0
    clock_running: bool = False
    # Internal elapsed match-seconds (1 real second = 1 match second)
    _elapsed_seconds: float = 0.0
    _run_started_at: float | None = None

    def score_line(self) -> str:
        return f"{self.home_score}-{self.away_score}"

    def live_elapsed_seconds(self) -> int:
        elapsed = self._elapsed_seconds
        if self.clock_running and self._run_started_at is not None:
            elapsed += time.time() - self._run_started_at
        return max(0, int(elapsed))

    def clock_display(self) -> str:
        """Scorebug time — live M:SS counter (no period labels like ET)."""
        if self.period in ("HT", "FT") and not self.clock_running:
            return self.period
        if self.stoppage > 0 and not self.clock_running:
            return f"{self.clock_minute}+{self.stoppage}'"
        total = self.live_elapsed_seconds()
        minutes, seconds = divmod(total, 60)
        # Cap display around a long match + ET
        minutes = min(minutes, 120)
        return f"{minutes}:{seconds:02d}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("_elapsed_seconds", None)
        d.pop("_run_started_at", None)
        d["score"] = self.score_line()
        d["clock"] = self.clock_display()
        d["clock_minute"] = min(120, self.live_elapsed_seconds() // 60)
        d["clock_running"] = self.clock_running
        return d


class MatchStore:
    """Live match / scorebug state — editable from the IBC editor."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = MatchState(
            home_team=config.HOME_TEAM,
            away_team=config.AWAY_TEAM,
            home_score=config.HOME_SCORE,
            away_score=config.AWAY_SCORE,
            period="1H",
            clock_minute=0,
            stoppage=0,
            clock_running=False,
        )

    def get(self) -> MatchState:
        with self._lock:
            return self._snapshot()

    def _sync_clock_fields(self) -> None:
        """Refresh derived minute from live elapsed (under lock)."""
        total = self._state.live_elapsed_seconds()
        self._state.clock_minute = min(120, total // 60)

    def _snapshot(self) -> MatchState:
        self._sync_clock_fields()
        s = self._state
        elapsed = s.live_elapsed_seconds()
        return MatchState(
            home_team=s.home_team,
            away_team=s.away_team,
            home_score=s.home_score,
            away_score=s.away_score,
            period=s.period,
            clock_minute=min(120, elapsed // 60),
            stoppage=s.stoppage,
            clock_running=s.clock_running,
            # Freeze elapsed for this snapshot so display doesn't double-count
            _elapsed_seconds=float(elapsed),
            _run_started_at=None,
        )

    def update(
        self,
        *,
        home_team: str | None = None,
        away_team: str | None = None,
        home_score: int | None = None,
        away_score: int | None = None,
        period: Period | None = None,
        clock_minute: int | None = None,
        stoppage: int | None = None,
    ) -> MatchState:
        with self._lock:
            if home_team is not None:
                self._state.home_team = (
                    home_team.strip().upper()[:12] or self._state.home_team
                )
            if away_team is not None:
                self._state.away_team = (
                    away_team.strip().upper()[:12] or self._state.away_team
                )
            if home_score is not None:
                self._state.home_score = max(0, min(99, home_score))
            if away_score is not None:
                self._state.away_score = max(0, min(99, away_score))
            if period is not None:
                self._state.period = period
            if stoppage is not None:
                self._state.stoppage = max(0, min(20, stoppage))
            if clock_minute is not None:
                # Manual minute set pauses and jumps the live clock
                if self._state.clock_running and self._state._run_started_at is not None:
                    self._state._elapsed_seconds += (
                        time.time() - self._state._run_started_at
                    )
                    self._state._run_started_at = None
                    self._state.clock_running = False
                self._state.clock_minute = max(0, min(120, clock_minute))
                self._state._elapsed_seconds = float(self._state.clock_minute * 60)
                self._state.stoppage = 0
            return self._snapshot()

    def start_clock(self) -> MatchState:
        """Kick off the live counter from 0:00."""
        with self._lock:
            self._state.period = "1H"
            self._state.stoppage = 0
            self._state.clock_minute = 0
            self._state._elapsed_seconds = 0.0
            self._state.clock_running = True
            self._state._run_started_at = time.time()
            return self._snapshot()

    def pause_clock(self) -> MatchState:
        with self._lock:
            if self._state.clock_running and self._state._run_started_at is not None:
                self._state._elapsed_seconds += (
                    time.time() - self._state._run_started_at
                )
                self._state._run_started_at = None
            self._state.clock_running = False
            self._sync_clock_fields()
            return self._snapshot()

    def reset_clock(self) -> MatchState:
        """Reset timer to 0:00 and stop."""
        with self._lock:
            self._state.clock_running = False
            self._state._run_started_at = None
            self._state._elapsed_seconds = 0.0
            self._state.clock_minute = 0
            self._state.stoppage = 0
            self._state.period = "1H"
            return self._snapshot()

    def add_goal(self, side: str) -> MatchState:
        side = side.lower()
        with self._lock:
            if side == "home":
                self._state.home_score = min(99, self._state.home_score + 1)
            elif side == "away":
                self._state.away_score = min(99, self._state.away_score + 1)
            else:
                raise ValueError("side must be 'home' or 'away'")
            return self._snapshot()


match_store = MatchStore()
