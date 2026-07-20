from __future__ import annotations

import threading
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

    def score_line(self) -> str:
        return f"{self.home_score}-{self.away_score}"

    def clock_display(self) -> str:
        """Scorebug time — minute / stoppage only (no period labels like ET)."""
        if self.period in ("HT", "FT"):
            return self.period
        if self.stoppage > 0:
            return f"{self.clock_minute}+{self.stoppage}'"
        return f"{self.clock_minute}'"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["score"] = self.score_line()
        d["clock"] = self.clock_display()
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
        )

    def get(self) -> MatchState:
        with self._lock:
            return self._snapshot()

    def _snapshot(self) -> MatchState:
        s = self._state
        return MatchState(
            home_team=s.home_team,
            away_team=s.away_team,
            home_score=s.home_score,
            away_score=s.away_score,
            period=s.period,
            clock_minute=s.clock_minute,
            stoppage=s.stoppage,
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
            if clock_minute is not None:
                self._state.clock_minute = max(0, min(120, clock_minute))
            if stoppage is not None:
                self._state.stoppage = max(0, min(20, stoppage))
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
