"""Deficit round robin: fair shares by bytes, not by turns, when items vary in size.

Round-robin scheduling across flows is fair only when every item
is the same size. Serve one item per flow per round and a flow
whose items are ten times larger walks away with ten times the
bandwidth, because a turn is not a byte and the flows that
matter, network flows, task payloads, are measured in bytes.
Deficit round robin fixes the unfairness without abandoning the
simple rotation. Each flow carries a deficit counter that gains a
fixed quantum of credit every round, and a flow may send an item
only when its deficit covers that item's size, spending the
deficit down as it sends and carrying the leftover into the next
round. A flow with large items saves its credit across rounds
until it can afford one, a flow with small items sends several
per round, and over time every flow receives bandwidth in
proportion to its quantum rather than to how it happens to
packetize, so the byte share is fair even though the turn count
is not. This module keeps the per-flow queues and deficits, runs
a round, and reports the bytes each flow was served, so the
fairness plain round robin lacks is a measured distribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class DeficitRoundRobin:
    quantum: int
    _queues: dict[str, list[int]] = field(default_factory=dict)
    _deficit: dict[str, int] = field(default_factory=dict)
    _order: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.quantum <= 0:
            raise Invalid("quantum must be positive")

    def enqueue(self, flow: str, size: int) -> None:
        if size <= 0:
            raise Invalid("item size must be positive")
        if flow not in self._queues:
            self._queues[flow] = []
            self._deficit[flow] = 0
            self._order.append(flow)
        self._queues[flow].append(size)

    def round(self) -> dict[str, int]:
        served: dict[str, int] = {}
        for flow in self._order:
            queue = self._queues[flow]
            if not queue:
                self._deficit[flow] = 0
                continue
            self._deficit[flow] += self.quantum
            sent = 0
            while queue and queue[0] <= self._deficit[flow]:
                size = queue.pop(0)
                self._deficit[flow] -= size
                sent += size
            if sent:
                served[flow] = sent
        return served

    def backlog(self, flow: str) -> int:
        return len(self._queues.get(flow, []))
