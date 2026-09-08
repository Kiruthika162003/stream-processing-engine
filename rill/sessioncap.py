"""Capped sessions: a gap closes an idle session, but only a cap closes a busy one.

A session window closes after a gap of silence, which works for
a user who eventually stops and is a trap for one who never does.
An account under a bot, a sensor stuck chattering, a replayed
log, any key that keeps producing events closer together than the
gap never falls silent, so its session never closes, its state
never flushes, and one session grows without bound while the gap
timer it is waiting on never fires. The fix is a maximum duration:
a session closes on the gap or once it has been open for the cap,
whichever comes first, so an idle key still closes on silence and
a relentless key is forced to close and flush on a schedule
regardless of how continuously it fires. The cap changes the
semantics slightly, since a genuinely long single session is now
split into pieces, but an unbounded session is not a semantic to
preserve, it is a memory leak with a business meaning. This
module tracks the open session per key, closes it on a gap or the
cap, and emits the closed span, so the difference between a
capped stream that flushes on schedule and an uncapped one that
never does is a measured count of closes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class CappedSessions:
    gap: int
    max_duration: int
    _open: dict[str, tuple[int, int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.gap <= 0 or self.max_duration <= 0:
            raise Invalid("gap and max_duration must be positive")

    def event(self, key: str, timestamp: int) -> tuple[int, int] | None:
        if key not in self._open:
            self._open[key] = (timestamp, timestamp)
            return None
        start, last = self._open[key]
        if timestamp - last >= self.gap:
            self._open[key] = (timestamp, timestamp)
            return (start, last)
        if timestamp - start >= self.max_duration:
            self._open[key] = (timestamp, timestamp)
            return (start, last)
        self._open[key] = (start, timestamp)
        return None

    def open_sessions(self) -> int:
        return len(self._open)
