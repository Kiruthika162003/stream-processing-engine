"""Triggers: when a window speaks, and how it labels what it says.

The watermark-only window speaks once, at the end, and for a
one-hour window that silence is a product decision nobody
made on purpose: the dashboard shows nothing for an hour and
then everything. Triggers split the utterance into labeled
firings: early firings are estimates, spoken every interval
while the window fills, the on-time firing is the answer,
spoken when the watermark passes, and each firing carries its
label because a number without one gets pasted into a report
as final by whoever finds it first. The accumulation mode is
the subtle knob: accumulating panes repeat the running total
and discarding panes speak only the delta, and mixing the two
in one pipeline double-counts revenue so reliably that this
module makes the mode a constructor argument and prints it in
every firing line.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

MODES = ("accumulating", "discarding")


@dataclass
class TriggeredPane:
    window_label: str
    interval: int
    mode: str
    total: int = 0
    spoken_since_firing: int = 0
    last_fire_at: int | None = None
    firings: list[str] = field(default_factory=list)
    sealed: bool = False

    def __post_init__(self) -> None:
        if self.interval <= 0:
            raise Invalid("the early interval must be positive")
        if self.mode not in MODES:
            raise Invalid(
                f"the mode is one of {MODES}; mixing them "
                "double-counts revenue"
            )

    def fold(self, value: int, now: int) -> str | None:
        if self.sealed:
            raise Invalid(
                f"{self.window_label} already spoke its answer"
            )
        self.total += value
        self.spoken_since_firing += value
        if (
            self.last_fire_at is None
            or now - self.last_fire_at >= self.interval
        ):
            return self._fire_early(now)
        return None

    def _fire_early(self, now: int) -> str:
        self.last_fire_at = now
        amount = (
            self.total
            if self.mode == "accumulating"
            else self.spoken_since_firing
        )
        self.spoken_since_firing = 0
        line = (
            f"ESTIMATE {self.window_label} = {amount} "
            f"({self.mode}); not final, whoever pastes this "
            "into a report was warned"
        )
        self.firings.append(line)
        return line

    def on_time(self) -> str:
        if self.sealed:
            raise Invalid("the answer was already spoken")
        self.sealed = True
        amount = (
            self.total
            if self.mode == "accumulating"
            else self.spoken_since_firing
        )
        line = (
            f"ANSWER {self.window_label} = {amount} "
            f"({self.mode}); the watermark passed and this "
            "label is the one that goes in the report"
        )
        self.firings.append(line)
        return line

    def transcript(self) -> str:
        if not self.firings:
            return f"{self.window_label}: silent so far"
        return "\n".join(self.firings)
