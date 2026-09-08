"""The skew meter: how late is this stream, as a distribution, not a feeling.

Every watermark bound is sized against out-of-orderness, and
out-of-orderness is usually described in war stories rather
than numbers, so the meter records the skew of every event,
arrival minus event time, and keeps the distribution the
bound should be sized against: percentiles of lateness, the
share that would be declared late under candidate bounds, and
the trend, because skew is not stationary, it breathes with
network weather and batch upstreams, and a bound sized on
last month's distribution quietly rots. The what-if table is
the deliverable: for each candidate bound, the percentage of
traffic it would refuse, read straight from the recorded
distribution, so the meeting about the bound starts from
"bound 5 refuses 2.1 percent of last week" instead of from
whoever tells the best outage story.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SkewMeter:
    skews: list[int] = field(default_factory=list)

    def observe(self, event_time: int, arrival: int) -> None:
        skew = arrival - event_time
        if skew < 0:
            raise Invalid(
                "arrival before the event means a clock is "
                "lying, and that is a different meter"
            )
        self.skews.append(skew)

    def percentile(self, rank: int) -> int:
        if not self.skews:
            raise Invalid("no skews observed")
        if not 1 <= rank <= 100:
            raise Invalid("percentiles run 1 to 100")
        ordered = sorted(self.skews)
        index = max(0, (rank * len(ordered) + 99) // 100 - 1)
        return ordered[index]

    def refusal_share(self, bound: int) -> float:
        if not self.skews:
            raise Invalid("no skews observed")
        refused = sum(1 for skew in self.skews if skew > bound)
        return 100 * refused / len(self.skews)

    def what_if_table(self, candidates: list[int]) -> str:
        if not candidates:
            raise Invalid("no candidate bounds")
        lines = [
            "the meeting starts here, not from the best "
            "outage story:"
        ]
        for bound in sorted(candidates):
            share = self.refusal_share(bound)
            lines.append(
                f"  bound {bound} refuses {share:.1f}% of "
                "this distribution"
            )
        lines.append(
            f"p50 skew {self.percentile(50)}, p99 "
            f"{self.percentile(99)}; sized against numbers, "
            "re-sized when they breathe"
        )
        return "\n".join(lines)
