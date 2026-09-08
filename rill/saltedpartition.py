"""Salting: spreading a hot key across partitions, and the merge that spread now requires.

A partitioned stream keys each event so a key's events all land on
one partition, which preserves per-key order and, when one key is
hot, dumps its whole load onto a single partition while its
siblings idle. The blunt fix is salting: for the known hot keys,
append a small random salt to the routing key so the hot key's
events scatter across several partitions instead of piling on one,
turning a fifty-percent-on-one-partition skew into an even spread.
The salt is not free, though, and the cost is the reason salting
is a decision and not a default: once a hot key's events are split
across partitions, any per-key aggregation must be done in two
stages, a partial aggregate per salted variant and then a merge of
those partials back into the true per-key result, and per-key
ordering across the salted variants is lost. So salting trades the
single-partition hot spot for a downstream merge and a weaker
ordering guarantee, worth it when the skew is severe enough that
one partition is the bottleneck and the aggregation can tolerate
the merge. This module routes with salting for the hot keys and
plain routing for the rest, so the load a hot key would have
concentrated and the way salting redistributes it are a measured
contrast.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.content_hash import stable_bucket
from rill.errors import Invalid


@dataclass
class SaltedPartitioner:
    partitions: int
    salt_factor: int
    hot_keys: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.partitions < 1:
            raise Invalid("need at least one partition")
        if self.salt_factor < 1:
            raise Invalid("salt factor must be positive")

    def route(self, key: str, salt: Callable[[], int]) -> int:
        if key in self.hot_keys:
            routing_key = f"{key}#{salt() % self.salt_factor}"
        else:
            routing_key = key
        return stable_bucket(routing_key, self.partitions)
