"""Per-key timers: the stream's way of acting on silence.

Events let a pipeline react to what happened; timers let it
react to what did not: the cart abandoned for thirty minutes,
the sensor quiet past its heartbeat, the payment that never
followed its order. A timer is set per key against event
time, fires when the watermark passes its deadline, and the
discipline is replacement: setting a timer for a key that
already holds one replaces it, because the common pattern,
push the deadline out on every event, would otherwise leak a
timer per event and fire a false alarm per leak. The timer
storm is the failure mode this module meters: a watermark
jump that matures thousands of timers at once turns one
quiet moment into a thundering callback herd, so firing
reports the herd size and the drill shows the jump, because
capacity planning for timers is planning for the jump, not
the average.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class TimerService:
    deadlines: dict[str, int] = field(default_factory=dict)
    replaced: int = 0
    fired_total: int = 0
    largest_herd: int = 0

    def set_timer(self, key: str, deadline: int) -> str:
        if not key:
            raise Invalid("a timer without a key calls nobody back")
        if deadline < 0:
            raise Invalid("deadlines live in event time, at zero or later")
        previous = self.deadlines.get(key)
        self.deadlines[key] = deadline
        if previous is not None:
            self.replaced += 1
            return (
                f"{key}: deadline moves {previous} -> "
                f"{deadline}; replaced, not stacked, or every "
                "event would leak a timer and every leak would "
                "fire a false alarm"
            )
        return f"{key}: timer set for {deadline}"

    def clear(self, key: str) -> str:
        if key not in self.deadlines:
            raise Invalid(f"{key} holds no timer to clear")
        del self.deadlines[key]
        return f"{key}: the awaited thing happened; timer cleared"

    def advance(self, watermark: int) -> list[str]:
        matured = sorted(
            (deadline, key)
            for key, deadline in self.deadlines.items()
            if deadline <= watermark
        )
        for _, key in matured:
            del self.deadlines[key]
        self.fired_total += len(matured)
        self.largest_herd = max(self.largest_herd, len(matured))
        return [
            f"{key}: silence lasted to {deadline}; firing"
            for deadline, key in matured
        ]

    def storm_report(self) -> str:
        return (
            f"{self.fired_total} firing(s), largest herd "
            f"{self.largest_herd}, {self.replaced} "
            f"replacement(s), {len(self.deadlines)} armed; "
            "capacity planning for timers is planning for the "
            "jump, not the average"
        )
