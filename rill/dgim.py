"""DGIM: counting the ones in a sliding window without storing the window.

Counting how many events in the last N ticks were hits is
trivial with the last N bits in hand and impossible to afford
when N is large and there are many such windows. DGIM keeps
only buckets: each bucket remembers the timestamp of its newest
one and a size that is always a power of two, the count of ones
it covers, and the invariant is that at most two buckets share
any size. A new one starts a size-one bucket, and whenever a
third bucket of some size appears the two oldest of that size
merge into one of double size, so the bucket count stays
logarithmic in N. Buckets whose newest one has aged out of the
window are dropped. The estimate sums every bucket's size but
counts only half of the oldest bucket, the one straddling the
window's edge, because that bucket's ones are partly expired and
half is the best guess for how many remain. That halving is the
whole error: the estimate is off by at most half the oldest
bucket's size, which is why the relative error stays bounded no
matter how the ones are arranged.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Dgim:
    window: int
    _now: int = -1
    _buckets: list[list[int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.window <= 0:
            raise Invalid("window must be positive")

    def observe(self, bit: int) -> None:
        if bit not in (0, 1):
            raise Invalid("DGIM counts bits, 0 or 1")
        self._now += 1
        self._expire()
        if bit == 0:
            return
        self._buckets.insert(0, [self._now, 1])
        self._collapse()

    def _expire(self) -> None:
        edge = self._now - self.window
        while self._buckets and self._buckets[-1][0] <= edge:
            self._buckets.pop()

    def _collapse(self) -> None:
        while True:
            by_size: dict[int, list[int]] = {}
            for index, bucket in enumerate(self._buckets):
                by_size.setdefault(bucket[1], []).append(index)
            crowded = [idxs for idxs in by_size.values() if len(idxs) >= 3]
            if not crowded:
                return
            ascending = sorted(crowded[0])
            oldest = ascending[-1]
            second_oldest = ascending[-2]
            self._buckets[second_oldest][1] *= 2
            del self._buckets[oldest]

    def estimate(self) -> int:
        self._expire()
        if not self._buckets:
            return 0
        total = sum(bucket[1] for bucket in self._buckets)
        oldest = self._buckets[-1][1]
        return total - oldest // 2

    def bucket_count(self) -> int:
        return len(self._buckets)
