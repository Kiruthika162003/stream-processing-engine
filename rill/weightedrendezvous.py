"""Weighted rendezvous: heavier nodes win more keys, in exact proportion to their weight.

Plain rendezvous hashing spreads keys evenly because every node is
equal, but real clusters are not: some nodes have more capacity
and should hold proportionally more of the keys. Weighted
rendezvous achieves that without a ring or virtual nodes by
bending the score each node computes for a key. Instead of the raw
hash, a node scores a key as its weight divided by the negative
natural log of the hash normalized to the open unit interval, and
the key goes to the highest score. That particular transform is
the trick: the negative-log term turns the uniform hash into an
exponential draw, and dividing by the weight rescales those draws
so that a node's chance of holding the largest score, and thus the
key, comes out exactly proportional to its weight. A node with
twice the weight wins about twice the keys, three times the weight
three times, with the same minimal-disruption property rendezvous
already has, since changing one node's weight or membership only
re-scores against that node. So heterogeneous capacity is
expressed as a weight and the placement follows, no manual sharding
and no virtual-node fudge factor to approximate a ratio. This
module scores and routes by weight, so the capacity-proportional
distribution is a measured split rather than an even one forced to
pretend.
"""

from __future__ import annotations

import math

from rill.content_hash import stable_digest
from rill.errors import Invalid


def _unit_hash(node: str, key: str) -> float:
    raw = int(stable_digest(f"{node}:{key}")[:12], 16)
    return (raw + 1) / (float(1 << 48) + 1)


def owner(key: str, weights: dict[str, float]) -> str:
    if not weights:
        raise Invalid("no nodes to route to")
    best_node = ""
    best_score = float("-inf")
    for node, weight in weights.items():
        if weight <= 0:
            raise Invalid(f"weight for {node} must be positive")
        score = weight / -math.log(_unit_hash(node, key))
        if score > best_score:
            best_score = score
            best_node = node
    return best_node
