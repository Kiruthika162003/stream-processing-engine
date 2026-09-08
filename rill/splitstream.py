"""Splitting a stream: one input, many typed outputs, no event unaccounted.

The opposite of union is the split, routing one stream into
several by a classifier, and the failure it invites is the
silent drop: a classifier with a case for orders and a case
for refunds meets an event that is neither, and if the split
has no default the event vanishes, which is the missing-data
bug that takes longest to find because nothing errored. The
splitter demands total coverage, either every event matches a
named output or a declared catch-all receives the rest, and it
refuses to run a classifier that can return a label with no
output, because an event routed to a nonexistent output is
dropped by a different name. The accounting is the proof:
events in must equal the sum across all outputs plus the
catch-all, checked continuously, because a split whose outputs
do not sum to its input has lost events somewhere and the sum
is the only thing that notices.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class StreamSplitter:
    outputs: tuple[str, ...]
    classify: Callable[[str], str]
    has_catch_all: bool = True
    routed: dict[str, int] = field(default_factory=dict)
    catch_all_count: int = 0
    total_in: int = 0

    def __post_init__(self) -> None:
        if not self.outputs:
            raise Invalid("a split needs at least one output")
        self.routed = dict.fromkeys(self.outputs, 0)

    def route(self, event: str) -> str:
        self.total_in += 1
        label = self.classify(event)
        if label in self.routed:
            self.routed[label] += 1
            return f"{event} -> {label}"
        if not self.has_catch_all:
            raise Invalid(
                f"{event} classified as {label!r}, which has "
                "no output and no catch-all; a silent drop is "
                "the missing-data bug that never errors"
            )
        self.catch_all_count += 1
        return (
            f"{event} -> catch-all (label {label!r} had no "
            "named output; accounted, not dropped)"
        )

    def accounting(self) -> str:
        summed = sum(self.routed.values()) + self.catch_all_count
        if summed != self.total_in:
            return (
                f"LOST: {self.total_in} in but outputs sum to "
                f"{summed}; the split lost events, and the sum "
                "is the only thing that notices"
            )
        return (
            f"{self.total_in} in, {summed} out (every event "
            "accounted); the sum is the proof nothing dropped"
        )
