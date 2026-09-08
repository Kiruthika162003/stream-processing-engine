"""Per-key order: the only ordering promise a parallel stream can keep.

Global order across a partitioned stream is a fiction that
costs a coordinator; per-key order is the promise that
matters and the one partitioning actually delivers, because
one key lives on one partition and one partition is a queue.
The auditor verifies the promise where it breaks in practice:
not in the partitions but in the seams, a rebalance that
moves a key mid-flight, a retry that overtakes the original,
an async sink that acknowledges out of order. It tracks the
last sequence seen per key, flags regressions with both
positions, and separates the two violation species: a
duplicate sequence is a retry echo, handled by idempotence,
while a backwards jump is a reordering, which idempotence
cannot fix and which usually means two copies of the key's
stream ran concurrently somewhere, the bug that makes
balances go negative in production and nowhere else.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class OrderAuditor:
    last_seen: dict[str, int] = field(default_factory=dict)
    echoes: list[str] = field(default_factory=list)
    reorderings: list[str] = field(default_factory=list)
    clean: int = 0

    def observe(self, key: str, sequence: int) -> str:
        if not key:
            raise Invalid("order is a per-key promise")
        if sequence < 0:
            raise Invalid("sequences start at zero")
        previous = self.last_seen.get(key)
        if previous is None or sequence == previous + 1:
            self.last_seen[key] = sequence
            self.clean += 1
            return f"{key}:{sequence} in order"
        if sequence == previous:
            self.echoes.append(f"{key}:{sequence}")
            return (
                f"{key}:{sequence} is a retry echo of "
                f"{previous}; idempotence handles this species"
            )
        if sequence < previous:
            self.reorderings.append(
                f"{key}: {previous} then {sequence}"
            )
            return (
                f"{key}:{sequence} arrived after {previous}: "
                "a reordering, which idempotence cannot fix, "
                "and which usually means two copies of this "
                "key's stream ran concurrently somewhere"
            )
        gap = sequence - previous - 1
        self.last_seen[key] = sequence
        return (
            f"{key}:{sequence} skipped {gap} sequence(s); a "
            "gap is a loss, not a reordering, and the loss "
            "has its own module"
        )

    def species_report(self) -> str:
        total = (
            self.clean
            + len(self.echoes)
            + len(self.reorderings)
        )
        if total == 0:
            raise Invalid("nothing observed")
        lines = [
            f"{self.clean} in order, {len(self.echoes)} "
            f"echo(es), {len(self.reorderings)} reordering(s)"
        ]
        for entry in self.reorderings:
            lines.append(
                f"  REORDERED {entry}: the bug that makes "
                "balances go negative in production and "
                "nowhere else"
            )
        return "\n".join(lines)
