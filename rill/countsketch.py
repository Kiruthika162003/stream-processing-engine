"""Count sketch: signed counters so collisions cancel instead of always inflating.

The count-min sketch answers frequency queries in fixed memory
and always overestimates, because every colliding key adds its
count into your cell and none subtracts, so the error is
one-directional and a rare key sharing a busy cell reads far
above its truth. The count sketch removes the bias with a sign.
Each row hashes a key to a bucket as before, but also to a sign,
plus or minus one, and updates add the signed count; a query
reads the cell, multiplies by the same sign, and takes the median
across rows. Now a colliding stranger lands in your cell with a
random sign, so in expectation its contribution cancels rather
than accumulates, and the estimate is unbiased, as likely a
little low as a little high, where count-min could only be high.
The median across rows is what tames the variance those random
signs introduce, since a few unlucky rows cannot move the middle.
The trade is that count sketch can underestimate, which count-min
never does, so a query that must never undercount still wants
count-min. This module keeps the signed tables and answers by
median, so the unbiased estimate is a measured contrast to the
one-sided inflation it replaces.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from rill.content_hash import stable_digest
from rill.errors import Invalid


@dataclass
class CountSketch:
    depth: int
    width: int
    _tables: list[list[int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.depth < 1 or self.width < 1:
            raise Invalid("depth and width must be positive")
        self._tables = [[0] * self.width for _ in range(self.depth)]

    def _bucket(self, row: int, key: str) -> int:
        return int(stable_digest(f"b{row}:{key}")[:8], 16) % self.width

    def _sign(self, row: int, key: str) -> int:
        return 1 if int(stable_digest(f"s{row}:{key}")[:8], 16) & 1 else -1

    def update(self, key: str, count: int = 1) -> None:
        for row in range(self.depth):
            self._tables[row][self._bucket(row, key)] += self._sign(row, key) * count

    def estimate(self, key: str) -> int:
        reads = [
            self._sign(row, key) * self._tables[row][self._bucket(row, key)]
            for row in range(self.depth)
        ]
        return int(statistics.median(reads))
