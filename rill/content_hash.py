"""One stable hash, shared by everything that routes.

Partition assignment, dedupe salts, and sampling decisions
all need the same property: the same string lands in the same
bucket on every machine, every restart, every version, which
is exactly the property Python's builtin hash gave up when it
grew per-process randomization. This module wraps sha256 into
the two shapes routing needs, a hex digest and a bucket
number, and every router in the package imports it from here,
because two routers with two hash functions agree only by
luck, and luck in routing expires on the busiest day of the
year.
"""

from __future__ import annotations

import hashlib

from rill.errors import Invalid


def stable_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def stable_bucket(text: str, buckets: int) -> int:
    if buckets < 1:
        raise Invalid("bucketing needs at least one bucket")
    return int(stable_digest(text)[:8], 16) % buckets
