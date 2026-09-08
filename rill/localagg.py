"""Local aggregation: fold before the shuffle, and the network thanks you.

The shuffle is the expensive hop, every event crossing the
network to its key's home worker, and pre-aggregation shrinks
it: each upstream worker folds its own events per key first,
then ships one partial per key per flush instead of one
message per event, and the downstream merge adds partials.
The savings depend entirely on the key distribution: a stream
of a few hot keys collapses beautifully, thousands of events
becoming a handful of partials, while a stream of unique keys
ships everything anyway plus the overhead of trying, which is
the honest caveat the combiner prints in its own bill. The
correctness rule is the one that bites in review: only
associative merges may pre-aggregate, sums and maxes and
counts, never means folded as means, and the guard refuses
the non-associative fold with the classic broken example in
the message, because the mean of means of unequal groups is
the bug every team writes exactly once.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

ASSOCIATIVE = ("sum", "max", "count")


@dataclass
class Combiner:
    fold: str
    partials: dict[str, int] = field(default_factory=dict)
    events_in: int = 0
    flushes: int = 0
    messages_shipped: int = 0

    def __post_init__(self) -> None:
        if self.fold not in ASSOCIATIVE:
            raise Invalid(
                f"{self.fold} does not pre-aggregate: only "
                "associative folds survive the merge, and the "
                "mean of means of unequal groups is the bug "
                "every team writes exactly once"
            )

    def add(self, key: str, value: int) -> None:
        self.events_in += 1
        held = self.partials.get(key)
        if held is None:
            self.partials[key] = (
                1 if self.fold == "count" else value
            )
        elif self.fold == "sum":
            self.partials[key] = held + value
        elif self.fold == "max":
            self.partials[key] = max(held, value)
        else:
            self.partials[key] = held + 1

    def flush(self) -> dict[str, int]:
        shipped = dict(self.partials)
        self.messages_shipped += len(shipped)
        self.flushes += 1
        self.partials.clear()
        return shipped

    def network_bill(self) -> str:
        if self.events_in == 0:
            raise Invalid("no events, no bill")
        naive = self.events_in
        actual = self.messages_shipped + len(self.partials)
        saved = naive - actual
        share = 100 * saved // naive
        line = (
            f"{naive} event(s) became {actual} message(s): "
            f"{saved} saved ({share}%)"
        )
        if share < 20:
            line += (
                "; mostly unique keys, so the shuffle shipped "
                "everything anyway plus the overhead of trying"
            )
        return line


def merge_partials(
    fold: str, batches: list[dict[str, int]]
) -> dict[str, int]:
    if fold not in ASSOCIATIVE:
        raise Invalid(f"{fold} partials cannot merge")
    merged: dict[str, int] = {}
    for batch in batches:
        for key, value in batch.items():
            held = merged.get(key)
            if held is None:
                merged[key] = value
            elif fold == "max":
                merged[key] = max(held, value)
            else:
                merged[key] = held + value
    return merged
