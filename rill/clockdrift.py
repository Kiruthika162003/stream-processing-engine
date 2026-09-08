"""Clock drift: the sources disagree about now, and event time inherits the lie.

Event time is only as honest as the clock that stamped it,
and producers' clocks drift: one runs three seconds fast,
another lags behind NTP, and their events arrive claiming
timestamps their own siblings would dispute. The drift
detector compares each source's event-time stamps against a
trusted reference at known sync points and estimates the
per-source offset, because an event three seconds early is
not out of order, it is time-traveling, and a watermark sized
for network skew will refuse it as late when it is actually
from the future. The correction is per source and applied,
not just reported, since detecting drift and leaving the
events crooked is diagnosis without treatment; the ledger
keeps the raw and corrected stamps both, because the day the
offset estimate is itself wrong, the raw stamp is the only
way back.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class DriftDetector:
    offsets: dict[str, int] = field(default_factory=dict)
    corrections: list[str] = field(default_factory=list)

    def sync(
        self, source: str, source_stamp: int, reference_stamp: int
    ) -> str:
        offset = source_stamp - reference_stamp
        self.offsets[source] = offset
        if offset == 0:
            return f"{source} is on time"
        direction = "fast" if offset > 0 else "slow"
        return (
            f"{source} runs {abs(offset)} tick(s) {direction}; "
            "an event that early is time-traveling, not out "
            "of order"
        )

    def correct(
        self, source: str, raw_event_time: int
    ) -> tuple[int, str]:
        if source not in self.offsets:
            raise Invalid(
                f"{source} never synced; correcting an "
                "unmeasured clock is guessing"
            )
        corrected = raw_event_time - self.offsets[source]
        self.corrections.append(
            f"{source}: raw {raw_event_time} -> {corrected}"
        )
        return corrected, (
            f"{raw_event_time} corrected to {corrected} "
            f"(offset {self.offsets[source]}); raw kept, "
            "because the offset estimate can itself be wrong"
        )

    def drift_report(self) -> str:
        if not self.offsets:
            raise Invalid("no sources synced")
        worst = max(
            self.offsets, key=lambda s: abs(self.offsets[s])
        )
        lines = [
            f"{len(self.offsets)} source(s) synced, worst "
            f"drift {worst} at {self.offsets[worst]} tick(s)"
        ]
        for source in sorted(self.offsets):
            lines.append(
                f"  {source}: offset {self.offsets[source]}"
            )
        lines.append(
            "detecting drift and leaving events crooked is "
            "diagnosis without treatment"
        )
        return "\n".join(lines)
