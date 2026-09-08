"""Raising the wide edge does nothing; raising the narrow one is the whole gain.

The drill builds a two-hop network, a source edge of capacity 5
into a sink edge of capacity 100, and measures the max flow, then
raises each edge in turn to see which moves the throughput. The
guess going in is that capacity is fungible, so adding to either
edge should help some. The measurement is sharper and one-sided:
the flow is 5, set entirely by the narrow source edge, and raising
the wide sink edge from 100 to 1000 leaves it at 5, because the
flow was never limited there, while raising the narrow source edge
to 50 lifts the whole flow to 50. The deposition keeps the fungible
guess beside the measured result, because the lesson is the
max-flow min-cut theorem made concrete: only the min-cut edge
repays more capacity, and capacity spent anywhere else is wasted.
It is the queueing lesson in a different shape, that the bottleneck
is the only thing worth widening, and everything else is a number
on a spreadsheet that does not move the throughput.
"""

from __future__ import annotations

from rill.maxflow import max_flow
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    base = max_flow({"s": {"a": 5}, "a": {"t": 100}}, "s", "t")
    widen_non_bottleneck = max_flow({"s": {"a": 5}, "a": {"t": 1000}}, "s", "t")
    widen_bottleneck = max_flow({"s": {"a": 50}, "a": {"t": 100}}, "s", "t")
    numbers = {
        "base_flow": base,
        "after_widening_wide_edge": widen_non_bottleneck,
        "after_widening_narrow_edge": widen_bottleneck,
    }
    holds = base == 5 and widen_non_bottleneck == 5 and widen_bottleneck == 50
    return Deposition(
        witness="bottleneck",
        claim=(
            "max flow was 5, set by the narrow source edge, and "
            "widening the wide sink edge to 1000 left it at 5 while "
            "widening the narrow edge to 50 lifted it to 50, so only "
            "the min-cut edge repays more capacity"
        ),
        numbers=numbers,
        holds=holds,
    )
