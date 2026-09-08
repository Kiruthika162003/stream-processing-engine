"""Approximate distinct counting: how many unique, in kilobytes not gigabytes.

Counting distinct values exactly, unique visitors, distinct
ips, cardinality of a key, needs to remember every value seen,
which for a high-cardinality stream is gigabytes; a
probabilistic cardinality estimator answers within a few
percent using a fixed small register array, trading exactness
for a memory bound that does not grow with the count. The
estimator's guarantee is symmetric, unlike a Bloom filter's:
its error is a percentage in both directions, so it can
report slightly high or slightly low, and the module prints
the estimate with its error band because a distinct count
quoted without one gets treated as exact and reconciled
against an exact count that will never match. The mergeability
is the property that makes it worth the approximation: two
estimators over two shards combine into one estimator for the
union without re-reading either shard's data, so a distinct
count across a fleet is the merge of per-node estimates, which
an exact count could never do without shipping every value to
one place.

The first estimator carried the classic small-range bias: a
single distinct value, setting one register and leaving the
rest zero, estimated dozens instead of one, because the
harmonic-mean formula is only unbiased once the registers
fill. The fix is the standard one, linear counting from the
zero-register count while the estimate is small, which pulls
one distinct back to one and leaves the large-count estimate
untouched, and the bias stays recorded here beside the
correction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from rill.content_hash import stable_digest
from rill.errors import Invalid

REGISTERS = 64


def _register_and_rank(item: str) -> tuple[int, int]:
    digest = stable_digest(item)
    value = int(digest, 16)
    register = value % REGISTERS
    remaining = value // REGISTERS
    rank = 1
    while remaining & 1 == 0 and rank < 32:
        rank += 1
        remaining >>= 1
    return register, rank


@dataclass
class CardinalityEstimator:
    registers: list[int] = field(
        default_factory=lambda: [0] * REGISTERS
    )

    def observe(self, item: str) -> None:
        register, rank = _register_and_rank(item)
        self.registers[register] = max(
            self.registers[register], rank
        )

    def estimate(self) -> int:
        harmonic = sum(2.0 ** -r for r in self.registers)
        if harmonic == 0:
            return 0
        raw = (REGISTERS ** 2) * 0.7 / harmonic
        zeros = self.registers.count(0)
        if raw <= 2.5 * REGISTERS and zeros:
            # small-range: linear counting corrects the bias
            # that made one distinct value estimate dozens
            return round(
                REGISTERS * math.log(REGISTERS / zeros)
            )
        return int(raw)

    def report(self, error_percent: int) -> str:
        estimate = self.estimate()
        band = estimate * error_percent // 100
        return (
            f"~{estimate} distinct (+/-{band}, "
            f"{error_percent}%); quoted with its band because "
            "a bare estimate gets reconciled against an exact "
            "count that will never match"
        )

    def merge(
        self, other: CardinalityEstimator
    ) -> CardinalityEstimator:
        if len(other.registers) != len(self.registers):
            raise Invalid(
                "estimators merge only at the same register "
                "width"
            )
        return CardinalityEstimator(
            registers=[
                max(a, b)
                for a, b in zip(
                    self.registers, other.registers, strict=True
                )
            ]
        )
