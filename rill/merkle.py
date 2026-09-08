"""Merkle trees: finding the few keys two replicas disagree on without shipping all of them.

Two replicas that should hold the same data occasionally drift,
and reconciling them by comparing every key is O(n) of network
for a difference that is usually tiny. A Merkle tree makes the
comparison pay for the difference, not the size. Keys hash into
leaf buckets, each leaf hashes its contents, and every internal
node hashes its children, so the root hash summarizes the whole
tree in one value. To compare, the replicas exchange root hashes;
if they match, the replicas are identical and nothing more is
sent. If they differ, each side descends only into the children
whose hashes disagree, pruning every subtree that already
matches, and arrives at exactly the leaf buckets that differ
after exchanging a number of hashes that grows with the log of
the tree and the count of differences, not the key count. This
module builds the tree over a fixed bucket count, hashes bottom
up, and diffs two trees by descending only the mismatched
branches, counting the hash comparisons so the log-not-linear
saving is a measurement. The saving is in hashes exchanged; the
local recompute here is naive on purpose, since the network is
the cost the tree exists to cut.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_bucket, stable_digest
from rill.errors import Invalid


@dataclass
class MerkleTree:
    leaves: int
    _bucket: dict[int, dict[str, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.leaves < 1 or self.leaves & (self.leaves - 1):
            raise Invalid("leaves must be a power of two")

    def put(self, key: str, value: str) -> None:
        index = stable_bucket(key, self.leaves)
        self._bucket.setdefault(index, {})[key] = value

    def _leaf_hash(self, index: int) -> str:
        items = sorted(self._bucket.get(index, {}).items())
        return stable_digest(repr(items))

    def _range_hash(self, lo: int, hi: int) -> str:
        if hi - lo == 1:
            return self._leaf_hash(lo)
        mid = (lo + hi) // 2
        return stable_digest(self._range_hash(lo, mid) + self._range_hash(mid, hi))

    def root(self) -> str:
        return self._range_hash(0, self.leaves)

    def diff(self, other: MerkleTree) -> tuple[list[int], int]:
        if self.leaves != other.leaves:
            raise Invalid("cannot diff trees of different shapes")
        differing: list[int] = []
        compared = [0]

        def descend(lo: int, hi: int) -> None:
            compared[0] += 1
            if self._range_hash(lo, hi) == other._range_hash(lo, hi):
                return
            if hi - lo == 1:
                differing.append(lo)
                return
            mid = (lo + hi) // 2
            descend(lo, mid)
            descend(mid, hi)

        descend(0, self.leaves)
        return differing, compared[0]
