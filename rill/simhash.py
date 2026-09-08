"""SimHash: a fingerprint where two documents that are similar differ in few bits.

MinHash estimates set overlap; SimHash answers a related question,
how similar two weighted feature sets are, and packs the answer
into a single fixed-width fingerprint whose bits can be compared
directly. Each feature hashes to a bit pattern, and for every bit
position the features vote, adding their weight if their hash has
a one there and subtracting it if a zero, so a position's final
bit is one when the weighted vote came out positive. The property
that makes this a locality-sensitive hash is that two feature sets
sharing most of their heavy features vote the same way on most
positions, so their fingerprints differ in only a few bits, while
unrelated sets vote independently and differ in about half. So the
Hamming distance between two SimHash fingerprints, the count of
differing bits, tracks the dissimilarity of the underlying sets,
and near-duplicate detection reduces to finding fingerprints
within a small Hamming distance, a cheap integer operation over
compact fingerprints rather than a comparison of the sets. Unlike
MinHash, which needs many hash values, SimHash is one integer per
document. This module builds the fingerprint and measures the
Hamming distance, so the small distance between similar documents
and the large distance between different ones is a measured
contrast.
"""

from __future__ import annotations

from rill.content_hash import stable_digest
from rill.errors import Invalid

_BITS = 64


def _feature_hash(feature: str) -> int:
    return int(stable_digest(feature)[:16], 16)


def simhash(features: dict[str, int]) -> int:
    if not features:
        raise Invalid("no features to hash")
    votes = [0] * _BITS
    for feature, weight in features.items():
        if weight < 0:
            raise Invalid("weights must be non-negative")
        digest = _feature_hash(feature)
        for bit in range(_BITS):
            if digest >> bit & 1:
                votes[bit] += weight
            else:
                votes[bit] -= weight
    fingerprint = 0
    for bit in range(_BITS):
        if votes[bit] > 0:
            fingerprint |= 1 << bit
    return fingerprint


def hamming_distance(left: int, right: int) -> int:
    return bin(left ^ right).count("1")
