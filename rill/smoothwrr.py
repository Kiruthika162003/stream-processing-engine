"""Smooth weighted round robin: the right ratio without the bursts naive weighting gives.

Sending requests to servers in proportion to their weights is
easy to get numerically right and easy to get temporally wrong.
The naive way, send a server as many consecutive requests as its
weight before moving on, produces the correct ratio over a full
cycle and a terrible distribution within it: the heavy server
gets a long unbroken burst while the light ones sit idle, then
the light ones fire, so the instantaneous load lurches even
though the totals balance. Smooth weighted round robin, the
scheme nginx uses, keeps the ratio and spreads the picks. Each
server carries a running credit that grows by its weight every
step; the server with the most credit is chosen and immediately
has the total weight subtracted from its credit, which pushes it
to the back of the line for a while proportional to how far ahead
it was. The result interleaves the servers so a weight of five
against a weight of one comes out spread through the cycle rather
than bunched at its front. This module runs the selection, so the
fair totals and the short runs are both measured against the
naive burst the smooth version is built to avoid.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SmoothWeightedRoundRobin:
    weights: dict[str, int]
    _current: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.weights:
            raise Invalid("need at least one server")
        if any(weight <= 0 for weight in self.weights.values()):
            raise Invalid("weights must be positive")
        self._current = dict.fromkeys(self.weights, 0)

    def pick(self) -> str:
        total = sum(self.weights.values())
        for server, weight in self.weights.items():
            self._current[server] += weight
        chosen = max(self._current, key=lambda s: self._current[s])
        self._current[chosen] -= total
        return chosen

    def cycle(self) -> list[str]:
        total = sum(self.weights.values())
        return [self.pick() for _ in range(total)]
