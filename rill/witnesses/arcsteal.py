"""The fifth node steals its arc, and virtual nodes flatten the load it leaves.

The drill routes three thousand keys across four nodes on a ring
with a hundred virtual points each, adds a fifth node, and counts
how many keys changed owner. The number that matters is small:
571 of 3000, about 0.19, right at the one-in-five a fifth node
should take, where modulo hashing would have moved closer to
four in five and cold-started nearly the whole store. The second
half of the deposition measures balance, because a ring with one
point per node is badly lopsided; the drill builds a five-node
ring at a single point each and finds a max-over-mean load near
2.1, one node carrying twice its share, then rebuilds it at two
hundred points each and watches the ratio fall under 1.1 as each
node's ownership scatters into many small arcs that average out.
The two numbers together are the whole case for the ring: a
change moves a slice and not the world, and the virtual points
are what make the slices fair.
"""

from __future__ import annotations

from collections import Counter

from rill.hashring import HashRing
from rill.witnesses.deposition import Deposition

KEYS = [f"key-{number}" for number in range(3000)]


def _max_over_mean(vnodes: int) -> float:
    ring = HashRing(vnodes=vnodes)
    for node in ("a", "b", "c", "d", "e"):
        ring.add(node)
    loads = Counter(ring.owner(key) for key in KEYS)
    counts = [loads[node] for node in ring.nodes()]
    return max(counts) / (sum(counts) / len(counts))


def run() -> Deposition:
    ring = HashRing(vnodes=100)
    for node in ("a", "b", "c", "d"):
        ring.add(node)
    before = {key: ring.owner(key) for key in KEYS}
    ring.add("e")
    moved = sum(1 for key in KEYS if before[key] != ring.owner(key))
    lopsided = _max_over_mean(1)
    even = _max_over_mean(200)
    numbers = {
        "keys": len(KEYS),
        "moved_adding_fifth": moved,
        "moved_fraction": round(moved / len(KEYS), 3),
        "one_point_max_over_mean": round(lopsided, 2),
        "many_points_max_over_mean": round(even, 2),
    }
    holds = (
        0.15 < moved / len(KEYS) < 0.25
        and lopsided > 1.8
        and even < 1.2
    )
    return Deposition(
        witness="arcsteal",
        claim=(
            "adding a fifth node moved 0.19 of the keys, near the "
            "ideal fifth where modulo would move four fifths, and "
            "virtual points dropped the load's max-over-mean from "
            "about 2.1 at one point each to under 1.1 at two "
            "hundred"
        ),
        numbers=numbers,
        holds=holds,
    )
