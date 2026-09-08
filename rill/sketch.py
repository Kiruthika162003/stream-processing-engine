"""The count-min sketch: every answer is an overestimate, and says by how much.

Counting distinct keys exactly is a dictionary; counting them
in fixed memory is a grid of counters and a bargain. Each key
increments one counter per row, chosen by that row's hash,
and a query reads its counters and returns the minimum, which
can only overestimate: collisions add strangers' counts to
your cell, never subtract, so the truth is at most the answer
and the answer is at most the truth plus the collision noise.
The width buys accuracy and the depth buys confidence, and
the sketch prints its own error budget, total stream weight
divided by width, next to every answer, because a count-min
answer quoted without its budget reads as exact to whoever
pastes it into the incident channel, and the overestimate
always surfaces at the worst moment, inflating precisely the
key someone is deciding whether to throttle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_bucket
from rill.errors import Invalid


@dataclass
class CountMin:
    width: int
    depth: int
    grid: list[list[int]] = field(default_factory=list)
    total_weight: int = 0

    def __post_init__(self) -> None:
        if self.width < 2 or self.depth < 1:
            raise Invalid(
                "the sketch needs width for accuracy and depth "
                "for confidence"
            )
        if not self.grid:
            self.grid = [
                [0] * self.width for _ in range(self.depth)
            ]

    def _cells(self, key: str) -> list[int]:
        return [
            stable_bucket(f"row{row}|{key}", self.width)
            for row in range(self.depth)
        ]

    def add(self, key: str, weight: int = 1) -> None:
        if weight < 1:
            raise Invalid("weight must be positive")
        for row, cell in enumerate(self._cells(key)):
            self.grid[row][cell] += weight
        self.total_weight += weight

    def estimate(self, key: str) -> int:
        return min(
            self.grid[row][cell]
            for row, cell in enumerate(self._cells(key))
        )

    def error_budget(self) -> int:
        return self.total_weight // self.width

    def answer(self, key: str) -> str:
        estimate = self.estimate(key)
        return (
            f"{key}: at most {estimate}, at least "
            f"{max(0, estimate - self.error_budget())} "
            f"(budget {self.error_budget()}); quoted without "
            "the budget this reads as exact"
        )

    def overestimate_audit(
        self, truth: dict[str, int]
    ) -> str:
        worst_key = ""
        worst_gap = -1
        for key, true_count in truth.items():
            gap = self.estimate(key) - true_count
            if gap < 0:
                return (
                    f"IMPOSSIBLE: {key} underestimated by "
                    f"{-gap}; count-min cannot subtract, the "
                    "sketch is corrupt"
                )
            if gap > worst_gap:
                worst_gap = gap
                worst_key = key
        return (
            f"worst overestimate {worst_gap} on {worst_key}, "
            f"budget {self.error_budget()}: "
            + (
                "inside the bargain"
                if worst_gap <= self.error_budget()
                else "OUTSIDE the stated budget, which the "
                "math says cannot happen often"
            )
        )
