"""MinHash: estimating how much two sets overlap from a handful of minimum hashes.

Comparing two large sets for their Jaccard similarity, the size of
their intersection over the size of their union, exactly means
holding both sets and intersecting them, which for a stream of
sets or a fleet of documents is too much memory and time. MinHash
estimates the same ratio from a tiny fixed-size signature. Pick a
fixed set of hash functions, and for each one keep only the
minimum hash value over all the set's elements; that vector of
minima is the signature. The trick is that for any one hash
function, the probability that two sets share the same minimum is
exactly their Jaccard similarity, because the element that hashes
smallest across the union is equally likely to fall in the
intersection as anywhere else. So the fraction of hash functions
on which two signatures agree is an unbiased estimate of the
Jaccard similarity, computed from k numbers per set instead of the
sets themselves, with error shrinking like one over the square
root of k. This is what backs near-duplicate detection at scale:
signatures are small, mergeable, and comparable in the size of the
signature, not the sets. This module builds the signature and
estimates the similarity, so the agreement-fraction estimate is a
measured approximation to a Jaccard computed the exact way.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_digest
from rill.errors import Invalid


@dataclass
class MinHash:
    num_hashes: int
    _signature: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.num_hashes < 1:
            raise Invalid("need at least one hash function")
        self._signature = [1 << 63] * self.num_hashes

    def add(self, item: str) -> None:
        for index in range(self.num_hashes):
            value = int(stable_digest(f"{index}:{item}")[:12], 16)
            self._signature[index] = min(self._signature[index], value)

    def signature(self) -> list[int]:
        return list(self._signature)


def similarity(left: MinHash, right: MinHash) -> float:
    a, b = left.signature(), right.signature()
    if len(a) != len(b):
        raise Invalid("signatures must be the same length")
    if not a:
        raise Invalid("empty signatures")
    agree = sum(1 for x, y in zip(a, b, strict=True) if x == y)
    return agree / len(a)
