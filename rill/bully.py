"""Bully election: the highest live id always wins, so a lower initiator gets overruled.

When a cluster loses its coordinator it must elect a new one, and
the bully algorithm picks by identity: the live node with the
highest id becomes leader. A node that notices the leader is gone
starts an election by messaging every node with a higher id than
its own; if any of them answers, the initiator steps aside,
bullied, because a higher node is alive and will run its own
election, and if none answers the initiator is the highest live
node and declares itself leader. The recursion resolves upward to
whoever is highest and alive, so the outcome does not depend on
who noticed the failure first, only on who has the largest id
among the survivors. That determinism is the point: every node
that runs the protocol agrees on the same leader without a vote or
a tiebreak, because the id order is total. The cost is chatter, a
low-id node that starts an election bothers every higher node, and
a flapping high node can trigger repeated elections, but the
result is always unambiguous. This module models the live set, the
leader as its maximum, and an election that returns the winner and
whether the initiator was overruled, so the bullying and the
deterministic outcome are a computed result rather than a protocol
sketch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class BullyElection:
    node_ids: tuple[int, ...]
    _down: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.node_ids:
            raise Invalid("need at least one node")

    def fail(self, node: int) -> None:
        if node not in self.node_ids:
            raise Invalid(f"unknown node {node}")
        self._down.add(node)

    def recover(self, node: int) -> None:
        self._down.discard(node)

    def alive(self) -> list[int]:
        return sorted(n for n in self.node_ids if n not in self._down)

    def leader(self) -> int:
        live = self.alive()
        if not live:
            raise Invalid("no live nodes; no leader")
        return live[-1]

    def start_election(self, initiator: int) -> tuple[int, bool]:
        if initiator not in self.node_ids:
            raise Invalid(f"unknown node {initiator}")
        if initiator in self._down:
            raise Invalid("a down node cannot start an election")
        higher_alive = [n for n in self.alive() if n > initiator]
        winner = self.leader()
        overruled = bool(higher_alive)
        return winner, overruled
