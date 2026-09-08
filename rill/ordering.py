"""Per-key ordering: the guarantee that survives partitioning, and the one that does not.

Streams promise per-key ordering, not global ordering, and
the distinction is the source of half the surprises in this
field: events for one key arrive in the order they were
produced, but events for different keys interleave freely, so
a consumer that assumes a global timeline is building on a
guarantee the system never made. The checker validates the
real promise, that within each key the sequence numbers are
monotonic, and reports a per-key violation as a genuine bug
while explicitly not flagging cross-key interleaving, because
flagging interleaving as disorder is how a correct system
gets debugged for a week chasing a non-problem. The subtle
real bug the checker does catch is a key whose events were
split across partitions, which breaks per-key order for that
key alone, and it names the key and the gap, since the fix is
in the partitioner and the symptom is one key's sequence
jumping backward.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class OrderChecker:
    last_seq: dict[str, int] = field(default_factory=dict)
    violations: list[str] = field(default_factory=list)
    checked: int = 0

    def observe(self, key: str, seq: int) -> str:
        if seq < 0:
            raise Invalid("sequence numbers are nonnegative")
        self.checked += 1
        previous = self.last_seq.get(key)
        if previous is not None and seq <= previous:
            self.violations.append(
                f"{key}: seq {seq} after {previous}, a "
                "backward jump that breaks per-key order"
            )
            self.last_seq[key] = max(previous, seq)
            return (
                f"VIOLATION {key}: {seq} <= {previous}; one "
                "key's order broke, look at the partitioner, "
                "not the whole timeline"
            )
        self.last_seq[key] = seq
        return f"{key} at {seq}, in order"

    def cross_key_note(self) -> str:
        return (
            f"{len(self.last_seq)} key(s) tracked; cross-key "
            "interleaving is not disorder and is not flagged, "
            "because chasing it debugs a non-problem for a week"
        )

    def verdict(self) -> str:
        if self.checked == 0:
            raise Invalid("nothing observed")
        if not self.violations:
            return (
                f"{self.checked} event(s) across "
                f"{len(self.last_seq)} key(s): per-key order "
                "held, and cross-key interleaving was correctly "
                "ignored"
            )
        return (
            f"{len(self.violations)} per-key violation(s) in "
            f"{self.checked} event(s); each is a real bug in "
            "the partitioner, not the timeline"
        )
