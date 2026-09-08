"""Local combiners: shrink the shuffle before it crosses the network.

The shuffle, moving keyed events to the operator that owns
their key, is a stream's largest network cost, and most of it
is avoidable: if a hundred events for one key sit on the same
upstream node, pre-aggregating them there sends one partial
result instead of a hundred events. The combiner runs before
the shuffle, folding same-key events into partials, and the
whole trick is that it only works for associative and
commutative aggregates, because the partials merge in
arbitrary order downstream, so the combiner refuses to
pre-aggregate a non-associative function rather than
producing a wrong answer fast. The savings are the point and
they are measured: events into the combiner against partials
out, the shuffle reduction as a ratio, because a combiner
that reduced ten thousand events to nine thousand partials
was not worth its own complexity and the ratio says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

ASSOCIATIVE = ("sum", "min", "max", "count")


@dataclass
class LocalCombiner:
    fold: str
    partials: dict[str, int] = field(default_factory=dict)
    events_in: int = 0

    def __post_init__(self) -> None:
        if self.fold not in ASSOCIATIVE:
            raise Invalid(
                f"{self.fold} is not associative; a combiner "
                "that pre-aggregates it produces a wrong answer "
                "fast"
            )

    def combine(self, key: str, value: int) -> None:
        self.events_in += 1
        if key not in self.partials:
            self.partials[key] = value
            return
        if self.fold == "min":
            self.partials[key] = min(self.partials[key], value)
        elif self.fold == "max":
            self.partials[key] = max(self.partials[key], value)
        else:
            self.partials[key] += value

    def emit(self) -> dict[str, int]:
        return dict(self.partials)

    def savings(self) -> str:
        partials_out = len(self.partials)
        if self.events_in == 0:
            raise Invalid("nothing combined")
        reduction = 1 - partials_out / self.events_in
        verdict = (
            "worth its complexity"
            if reduction >= 0.5
            else "barely reducing; reconsider whether the "
            "combiner earns its place"
        )
        return (
            f"{self.events_in} event(s) in, {partials_out} "
            f"partial(s) out, shuffle cut {reduction:.0%}; "
            f"{verdict}"
        )
