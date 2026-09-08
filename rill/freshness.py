"""The freshness budget: one SLO, split across stages, with the overspender named.

End-to-end freshness, event to queryable, is the promise
users experience, and it is spent in pieces nobody owns until
the split is written down: ingest takes its share, the
shuffle takes its share, the window waits its watermark
bound, the sink batches its flush interval, and the sum must
fit inside the SLO with margin for the bad day. The waterfall
makes the split a budget: each stage declares its allocation,
measured spend is compared per stage, and the overspender is
named by line item, because "we miss the freshness SLO" is a
meeting while "the sink's flush interval spends 40 of our
60-second budget" is a config change. The margin rule is the
adult one: allocations summing to exactly the SLO leave
nothing for the bad day, and the waterfall refuses the
zero-margin split with the sentence every SLO owner learns
once.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

MARGIN_SHARE = 10


@dataclass
class FreshnessWaterfall:
    slo: int
    allocations: dict[str, int] = field(default_factory=dict)
    spends: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.slo < 1:
            raise Invalid("an SLO needs a number")

    def allocate(self, stage: str, share: int) -> str:
        if share < 1:
            raise Invalid("allocations are positive")
        total = sum(self.allocations.values()) + share
        margin = self.slo - total
        if margin < self.slo * MARGIN_SHARE // 100:
            raise Invalid(
                f"allocations total {total} against an SLO of "
                f"{self.slo}: nothing left for the bad day, "
                "the sentence every SLO owner learns once"
            )
        self.allocations[stage] = share
        return (
            f"{stage} allocated {share}, margin {margin} "
            "remains for the bad day"
        )

    def spend(self, stage: str, measured: int) -> None:
        if stage not in self.allocations:
            raise Invalid(f"{stage} has no allocation")
        self.spends[stage] = measured

    def waterfall_report(self) -> str:
        if not self.spends:
            raise Invalid("nothing measured yet")
        lines = ["the waterfall, line item by line item:"]
        total_spend = 0
        worst_over = None
        for stage in self.allocations:
            allocated = self.allocations[stage]
            spent = self.spends.get(stage, 0)
            total_spend += spent
            over = spent - allocated
            marker = ""
            if over > 0:
                marker = f" OVER by {over}"
                if worst_over is None or over > worst_over[1]:
                    worst_over = (stage, over)
            lines.append(
                f"  {stage}: {spent} of {allocated}{marker}"
            )
        lines.append(
            f"end to end: {total_spend} of {self.slo}"
        )
        if worst_over:
            stage, over = worst_over
            lines.append(
                f"the overspender is {stage}, a config "
                "change, where missing the SLO is a meeting"
            )
        return "\n".join(lines)
