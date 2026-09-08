"""Probabilistic dedupe: trade a little wrong for a lot of memory back.

Exact deduplication remembers every id, which for a
high-volume stream is unbounded memory; a Bloom filter
remembers a fixed bitmap and trades exactness for it, and the
trade has a precise and one-directional shape that teams
misremember. A Bloom filter never says seen for an id it has
not seen, so it never drops a genuinely new event, but it can
say seen for a new id whose bits collide, so it can drop a new
event as a false duplicate. The direction is the whole design
decision: Bloom dedupe is safe when a false drop is tolerable
and a false pass is not, wrong when the reverse. The module
computes the false-positive rate from the bitmap size and the
count inserted, and refuses to keep inserting past the point
where that rate crosses the caller's tolerance, because a
Bloom filter silently filling past its design load is a dedupe
whose error rate is climbing invisibly toward useless.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_digest
from rill.errors import Invalid

BITS = 512
HASHES = 3


def _positions(item: str) -> list[int]:
    digest = stable_digest(item)
    return [
        int(digest[8 * index : 8 * index + 8], 16) % BITS
        for index in range(HASHES)
    ]


@dataclass
class BloomDeduper:
    max_false_positive: float
    bitmap: set[int] = field(default_factory=set)
    inserted: int = 0

    def __post_init__(self) -> None:
        if not 0 < self.max_false_positive < 1:
            raise Invalid(
                "the tolerable false-positive rate is a "
                "fraction strictly between 0 and 1"
            )

    def false_positive_rate(self) -> float:
        filled = len(self.bitmap) / BITS
        return filled ** HASHES

    def offer(self, item: str) -> bool:
        positions = _positions(item)
        if all(pos in self.bitmap for pos in positions):
            return False
        if self.false_positive_rate() >= self.max_false_positive:
            raise Invalid(
                f"the filter is full: false-positive rate "
                f"{self.false_positive_rate():.2%} has crossed "
                f"the {self.max_false_positive:.2%} tolerance, "
                "and inserting more climbs invisibly toward "
                "useless"
            )
        self.bitmap.update(positions)
        self.inserted += 1
        return True

    def guarantee(self) -> str:
        return (
            f"{self.inserted} inserted, false-positive rate "
            f"{self.false_positive_rate():.2%}; never drops a "
            "genuinely new event, may drop a colliding one, so "
            "safe only when a false drop beats a false pass"
        )
