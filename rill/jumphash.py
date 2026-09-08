"""Jump consistent hash: a bucket for a key from a formula, no ring and no memory at all.

The hash ring and rendezvous hashing both keep a data structure,
node positions or a node list, to route a key. Jump consistent
hash keeps nothing. Given a key and a bucket count it computes the
bucket with a short loop over a pseudo-random sequence seeded by
the key, and the loop's arithmetic guarantees two properties for
free: the keys spread evenly across the buckets, and when the
bucket count grows by one, only about one key in the new total
moves, the minimal disruption a consistent hash promises, achieved
with no stored state and in time that grows with the log of the
bucket count. The formula works by asking, as the bucket count
climbs, at which counts this key would jump to a newly added
bucket, and the last such jump below the target count is the
answer. The catch that distinguishes it from the ring is
structural: jump hash addresses buckets by number zero to n minus
one, so it can add or remove only the highest-numbered bucket,
not an arbitrary one in the middle, which fits a system that
scales its shard count up and down but not one where a specific
named node fails. This module computes the bucket, so the even
spread and the one-in-n movement on a resize are measurements
against a structure that stores nothing.
"""

from __future__ import annotations

from rill.content_hash import stable_digest
from rill.errors import Invalid

_MASK64 = (1 << 64) - 1


def _hash_key(key: str) -> int:
    return int(stable_digest(key)[:16], 16)


def jump_hash(key: str, buckets: int) -> int:
    if buckets < 1:
        raise Invalid("need at least one bucket")
    state = _hash_key(key)
    bucket = -1
    jump = 0
    while jump < buckets:
        bucket = jump
        state = (state * 2862933555777941757 + 1) & _MASK64
        jump = int((bucket + 1) * (float(1 << 31) / float((state >> 33) + 1)))
    return bucket
