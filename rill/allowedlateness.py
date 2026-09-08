"""Allowed lateness: the window keeps its state a while after it fires.

Firing a window and immediately discarding its state is the
strict policy, and it makes every late event a total loss;
allowed lateness is the compromise, keeping the window's
state for a grace period after the watermark passes so a
straggler that arrives within the grace updates the answer
and re-fires, and only after the grace expires is the state
finally dropped. The re-fire is a correction, labeled, so
downstream distinguishes the updated answer from a new one,
and the memory cost is explicit: allowed lateness is state
held past its usefulness for most windows to catch the few
that straggle, so the grace is a knob priced in retained
panes, not a free safety margin. The window that drops its
state reports the loss when a too-late event arrives, because
a straggler past the grace is a real dropped update and
pretending otherwise is how the count silently drifts.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class LatenessWindow:
    window_end: int
    allowed_lateness: int
    total: int = 0
    fired: bool = False
    state_dropped: bool = False
    fire_count: int = 0
    dropped_updates: int = 0

    def __post_init__(self) -> None:
        if self.allowed_lateness < 0:
            raise Invalid("allowed lateness cannot be negative")

    def add(self, value: int, watermark: int) -> str:
        if self.state_dropped:
            self.dropped_updates += 1
            return (
                "too late: the grace expired and the state is "
                "gone; a real dropped update, not a rounding "
                "error"
            )
        self.total += value
        if watermark >= self.window_end:
            self.fire_count += 1
            if self.fired:
                return (
                    f"re-fire (CORRECTION): total now "
                    f"{self.total}; a straggler updated the "
                    "answer within the grace"
                )
            self.fired = True
            return f"fire: total {self.total}"
        return f"accumulating: {self.total}"

    def maybe_drop(self, watermark: int) -> str:
        if self.state_dropped:
            return "state already dropped"
        if watermark > self.window_end + self.allowed_lateness:
            self.state_dropped = True
            return (
                f"state dropped at watermark {watermark}; the "
                f"grace of {self.allowed_lateness} bought "
                f"{self.fire_count} firing(s), and it was "
                "memory held past usefulness for most to catch "
                "the few"
            )
        remaining = (
            self.window_end + self.allowed_lateness - watermark
        )
        return f"grace holds, {remaining} tick(s) of lateness left"
