"""Size-tiered LSM: the tier size trades bytes rewritten against runs to search.

A log-structured merge tree turns random writes into sequential
ones by flushing sorted runs and merging them later, and the
size-tiered policy merges runs once enough of the same size have
piled up. How many is enough is the tier, and it is a dial
between the two amplifications that dominate an LSM's cost. A
small tier merges eagerly, so runs are folded together often and
few coexist, which keeps a point lookup cheap because it checks
few runs, but every merge rewrites the data it touches, so the
same key is written and rewritten many times and the write
amplification climbs. A large tier merges lazily, so a key is
rewritten far less often and the write amplification falls, but
many runs coexist and a lookup that finds nothing must check all
of them, so the read amplification climbs instead. Neither
setting wins both, which is why the tier is exposed and not
defaulted. This module simulates the flushes and the cascading
merges, counting the bytes written and the runs left standing, so
the write-for-read trade the tier sets is a pair of measured
numbers rather than a rule of thumb.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SizeTieredLSM:
    tier: int
    _runs: list[int] = field(default_factory=list)
    _bytes_written: int = 0
    _ingested: int = 0

    def __post_init__(self) -> None:
        if self.tier < 2:
            raise Invalid("tier must be at least two")

    def flush(self, size: int = 1) -> None:
        if size <= 0:
            raise Invalid("flush size must be positive")
        self._runs.append(size)
        self._bytes_written += size
        self._ingested += size
        self._compact()

    def _compact(self) -> None:
        while True:
            counts = Counter(self._runs)
            merges = [s for s, n in counts.items() if n >= self.tier]
            if not merges:
                return
            size = merges[0]
            for _ in range(self.tier):
                self._runs.remove(size)
            merged = size * self.tier
            self._runs.append(merged)
            self._bytes_written += merged

    def read_amplification(self) -> int:
        return len(self._runs)

    def write_amplification(self) -> float:
        if self._ingested == 0:
            raise Invalid("nothing ingested yet")
        return self._bytes_written / self._ingested
