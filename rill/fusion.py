"""Operator fusion: fewer hops, larger blast radius, and the arithmetic between.

Two operators wired in sequence can run as two stages with a
channel between them or fuse into one stage that calls both
functions per event, and the trade is mechanical: fusion
deletes the hop, its serialization and its queue, but welds
the operators' fates, one worker doing both jobs, one failure
domain, one parallelism setting for two workloads. The
planner prices each candidate pair: the hop saved is pure
profit when both operators are cheap and similarly parallel,
and the weld is pure loss when one operator needs forty
workers and the other four, because fusing them runs the
light one at the heavy one's width, ten workers doing nothing
in every slot. The verdict names the pair, the saving, and
the width mismatch, since fuse-everything and fuse-nothing
are both defaults, and defaults are what this module exists
to interrogate.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from rill.errors import Invalid

HOP_COST_PER_EVENT = 2


@dataclass(frozen=True)
class Stage:
    name: str
    ticks_per_event: int
    ideal_workers: int

    def __post_init__(self) -> None:
        if self.ticks_per_event < 1 or self.ideal_workers < 1:
            raise Invalid(
                f"{self.name} needs positive cost and width"
            )


def fusion_verdict(
    upstream: Stage, downstream: Stage, events: int
) -> str:
    if events < 1:
        raise Invalid("price fusion against actual traffic")
    hop_saved = events * HOP_COST_PER_EVENT
    width_ratio = max(
        upstream.ideal_workers, downstream.ideal_workers
    ) / min(upstream.ideal_workers, downstream.ideal_workers)
    pair = f"{upstream.name}+{downstream.name}"
    if width_ratio <= 2:
        return (
            f"FUSE {pair}: saves {hop_saved} hop tick(s) per "
            f"{events} event(s), widths "
            f"{upstream.ideal_workers} and "
            f"{downstream.ideal_workers} weld without waste"
        )
    idle_fraction = 1 - 1 / width_ratio
    return (
        f"KEEP THE HOP {pair}: the weld runs the light "
        f"operator at the heavy one's width, "
        f"{idle_fraction:.0%} of its slots idle; the "
        f"{hop_saved} hop tick(s) are real and this waste is "
        "bigger"
    )


def plan_chain(
    stages: list[Stage], events: int
) -> str:
    if len(stages) < 2:
        raise Invalid("fusion needs a chain")
    lines = ["the defaults, interrogated pair by pair:"]
    fused = kept = 0
    for upstream, downstream in pairwise(stages):
        verdict = fusion_verdict(upstream, downstream, events)
        if verdict.startswith("FUSE"):
            fused += 1
        else:
            kept += 1
        lines.append(f"  {verdict}")
    lines.append(
        f"{fused} weld(s), {kept} hop(s) kept; "
        "fuse-everything and fuse-nothing are both defaults"
    )
    return "\n".join(lines)
