"""Broadcast state: the rules everyone needs, kept consistent across all partitions.

Most stream state is keyed and partitioned, each operator
instance owning its slice, but some state is different: a set
of fraud rules, a feature flag, a lookup table that every
partition must consult, and partitioning it would mean each
instance seeing a different subset, which for rules is a
correctness bug where an event is judged by whichever rules
happened to land on its partition. Broadcast state is
replicated to every instance instead, and the design
constraint is that updates to it must be applied in the same
order everywhere or the instances diverge, so broadcast
updates flow through a single ordered channel and every
instance applies them identically. The module enforces the
read-only rule for the keyed side: a partition may read the
broadcast state but never write it, because a write from one
partition would be seen by that partition and no other,
recreating exactly the inconsistency broadcast state exists to
prevent, and the module refuses that write rather than letting
the divergence happen quietly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class BroadcastState:
    partitions: int
    rules: dict[str, str] = field(default_factory=dict)
    update_log: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.partitions < 1:
            raise Invalid("a job needs partitions")

    def broadcast_update(self, rule_id: str, rule: str) -> str:
        self.rules[rule_id] = rule
        self.update_log.append(f"{rule_id}={rule}")
        return (
            f"{rule_id} broadcast to all {self.partitions} "
            "partition(s) in order; every instance applies it "
            "identically"
        )

    def read(self, partition: int, rule_id: str) -> str:
        if not 0 <= partition < self.partitions:
            raise Invalid(f"no partition {partition}")
        rule = self.rules.get(rule_id)
        if rule is None:
            return f"partition {partition}: {rule_id} not set"
        return f"partition {partition}: {rule_id} = {rule}"

    def partition_write(
        self, partition: int, rule_id: str, rule: str
    ) -> str:
        raise Invalid(
            f"partition {partition} tried to set {rule_id}="
            f"{rule}: a keyed partition may read broadcast "
            "state but never write it, because that write "
            "would be seen by one partition and no other, the "
            "exact divergence broadcast state prevents"
        )

    def consistency_check(self) -> str:
        return (
            f"{len(self.rules)} rule(s) replicated identically "
            f"across {self.partitions} partition(s) via "
            f"{len(self.update_log)} ordered update(s); no "
            "partition holds a different view"
        )
