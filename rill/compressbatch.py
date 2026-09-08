"""Batch compression: bigger crates squeeze better, and the curve says why.

Compression works on redundancy, and redundancy accumulates
with batch size: a single event compresses barely, a hundred
similar events share their schema, their keys, their
repeated field names, and the ratio climbs, so the batch size
knob set for latency also quietly sets the network bill. The
model uses the honest curve, a fixed per-batch header plus a
marginal cost per event that shrinks with batch size toward
the entropy floor, and the table it prints puts the elbows
on display: the jump from 1 to 10 events per batch buys most
of the ratio, 10 to 100 buys the rest, and 100 to 1000 buys
almost nothing while making every retry ten times heavier,
which is the tradeoff hiding behind "just batch more".
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

HEADER_BYTES = 40
RAW_EVENT_BYTES = 100
ENTROPY_FLOOR = 22


@dataclass(frozen=True)
class CompressionModel:
    def compressed_size(self, batch_size: int) -> int:
        if batch_size < 1:
            raise Invalid("a batch holds at least one event")
        total = HEADER_BYTES
        for position in range(batch_size):
            shared = min(position, 10)
            marginal = max(
                ENTROPY_FLOOR,
                RAW_EVENT_BYTES - 7 * shared,
            )
            total += marginal
        return total

    def ratio(self, batch_size: int) -> float:
        raw = batch_size * RAW_EVENT_BYTES
        return raw / self.compressed_size(batch_size)

    def elbow_table(self, sizes: list[int]) -> str:
        if len(sizes) < 2:
            raise Invalid("the elbows need points")
        lines = ["the elbows, on display:"]
        previous_ratio = None
        for size in sorted(sizes):
            ratio = self.ratio(size)
            gain = (
                ""
                if previous_ratio is None
                else f" (+{ratio - previous_ratio:.2f})"
            )
            lines.append(
                f"  batch {size}: ratio {ratio:.2f}{gain}, "
                f"retry weight {self.compressed_size(size)} "
                "byte(s)"
            )
            previous_ratio = ratio
        lines.append(
            "the last jump buys almost nothing while making "
            "every retry heavier; the tradeoff hiding behind "
            "just-batch-more"
        )
        return "\n".join(lines)
