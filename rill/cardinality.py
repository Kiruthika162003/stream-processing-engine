"""Distinct counting in fixed memory: the census taker who samples ballots.

How many unique users did the stream see is a question whose
exact answer costs a set the size of the users, so linear
counting spends a fixed bitmap instead: each identity flips
its hashed bit, and the estimate reads the emptiness, since
the fraction of bits still zero shrinks predictably as
distinct identities arrive. The formula, buckets times the
natural log of buckets over empty buckets, corrects for
collisions honestly, and the module publishes its operating
envelope with every estimate: comfortable while the bitmap
stays under about half full, degrading as it saturates, and
refusing outright at full, because a saturated bitmap does
not estimate anymore, it just says "many", and the difference
between an estimate and the word many is the entire product.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from rill.content_hash import stable_bucket
from rill.errors import Invalid


@dataclass
class LinearCounter:
    buckets: int
    bitmap: set[int] = field(default_factory=set)
    offered: int = 0

    def __post_init__(self) -> None:
        if self.buckets < 16:
            raise Invalid(
                "a bitmap under 16 bits is a mood ring"
            )

    def offer(self, identity: str) -> None:
        if not identity:
            raise Invalid("distinctness needs identity")
        self.offered += 1
        self.bitmap.add(stable_bucket(identity, self.buckets))

    def estimate(self) -> int:
        empty = self.buckets - len(self.bitmap)
        if empty == 0:
            raise Invalid(
                "the bitmap is saturated; it no longer "
                "estimates, it just says many, and the "
                "difference is the entire product"
            )
        return round(
            self.buckets * math.log(self.buckets / empty)
        )

    def envelope(self) -> str:
        fill = len(self.bitmap) / self.buckets
        if fill == 1.0:
            return "saturated: the counter says many, not a number"
        state = (
            "comfortable"
            if fill <= 0.5
            else "degrading toward many"
        )
        return (
            f"{fill:.0%} full, {state}; estimate "
            f"{self.estimate()} from {self.offered} offer(s)"
        )
