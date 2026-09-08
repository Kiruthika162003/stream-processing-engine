"""Gossip dissemination: a rumor reaches everyone in log-many rounds, and survives loss.

Broadcasting a piece of state to every node by building a tree
is fast, one pass of depth log n, and brittle: kill an interior
node and its whole subtree never hears the news. Gossip trades
that speed for robustness. Each round every node that already
knows the rumor tells a few random peers, so the count of
informed nodes roughly multiplies each round and the rumor
saturates the cluster in a number of rounds that grows with the
log of the size, not the size, while depending on no particular
node to relay it: the same redundancy that makes gossip send more
messages than a tree is what lets it route around any node that
fails. The fanout is the dial. A fanout of one is a random walk
that crawls, and raising it multiplies the informed set faster
and reaches everyone in fewer rounds at the cost of more messages
per round. This module runs the rounds against an injected random
source so the saturation curve is reproducible, and reports the
rounds to cover the cluster, so the log-not-linear spread is a
measurement rather than a claim from a paper.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


def rounds_to_cover(size: int, fanout: int, peer: Callable[[int], int]) -> int:
    if size < 1:
        raise Invalid("cluster needs at least one node")
    if fanout < 1:
        raise Invalid("fanout must be at least one")
    informed = {0}
    rounds = 0
    while len(informed) < size:
        rounds += 1
        freshly: set[int] = set()
        for _ in informed:
            for _ in range(fanout):
                freshly.add(peer(size))
        informed |= freshly
        if rounds > size:
            raise Invalid("dissemination stalled; check the peer source")
    return rounds


def coverage_after(
    size: int, fanout: int, peer: Callable[[int], int], rounds: int
) -> int:
    if size < 1 or fanout < 1 or rounds < 0:
        raise Invalid("size and fanout must be positive, rounds non-negative")
    informed = {0}
    for _ in range(rounds):
        freshly: set[int] = set()
        for _ in informed:
            for _ in range(fanout):
                freshly.add(peer(size))
        informed |= freshly
    return len(informed)
