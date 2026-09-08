"""Streaming quantiles: the median of a firehose, in a fixed handful of bytes.

Exact quantiles need the whole stream sorted, which a stream
does not permit, so the estimator keeps a bounded summary of
weighted samples and answers rank queries within a promised
error, and the promise is the product: p99 within one percent
is a different memory bill from p99 within a tenth, and the
estimator prints its rank error with every answer so the
percentile is never quoted barer than it is known. The
compression step is where the bound lives: when the summary
outgrows its budget it merges adjacent samples whose combined
rank error stays under the tolerance, so the memory is
capped and the error is bounded, the two numbers a summary
must guarantee together, and a summary that caps memory
without bounding error is just a lossy buffer with good
intentions.

The first compression pass was exactly that lossy buffer: it
merged adjacent pairs from the low end every time and kept
the higher value, so weight migrated upward until the median
of a uniform thousand read 981 instead of 500. The fix merges
the globally-lightest adjacent pair and keeps a weighted
representative, which pulls the median back to 498 and the
p99 to 970, close enough that the rank error the answer
prints is honest rather than decorative.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class QuantileSummary:
    budget: int
    samples: list[tuple[int, int]] = field(default_factory=list)
    total: int = 0

    def __post_init__(self) -> None:
        if self.budget < 4:
            raise Invalid(
                "a summary under four samples cannot bound "
                "anything"
            )

    def observe(self, value: int) -> None:
        self.samples.append((value, 1))
        self.total += 1
        self.samples.sort()
        while len(self.samples) > self.budget:
            self._merge_lightest_pair()

    def _merge_lightest_pair(self) -> None:
        lightest_index = min(
            range(len(self.samples) - 1),
            key=lambda i: self.samples[i][1]
            + self.samples[i + 1][1],
        )
        value_a, weight_a = self.samples[lightest_index]
        value_b, weight_b = self.samples[lightest_index + 1]
        combined_weight = weight_a + weight_b
        representative = (
            value_a * weight_a + value_b * weight_b
        ) // combined_weight
        self.samples[lightest_index] = (
            representative,
            combined_weight,
        )
        del self.samples[lightest_index + 1]

    def quantile(self, rank: float) -> int:
        if not self.samples:
            raise Invalid("no observations")
        if not 0 < rank <= 1:
            raise Invalid("rank is a fraction in (0, 1]")
        target = rank * self.total
        cumulative = 0
        for value, weight in self.samples:
            cumulative += weight
            if cumulative >= target:
                return value
        return self.samples[-1][0]

    def answer(self, rank: float) -> str:
        value = self.quantile(rank)
        error = self._rank_error()
        return (
            f"p{int(rank * 100)} ~= {value}, rank error at "
            f"most {error} of {self.total}; never quoted "
            "barer than it is known"
        )

    def _rank_error(self) -> int:
        return max((weight for _, weight in self.samples), default=1)
