"""Consumer rebalancing: the group re-deals the partitions, ideally quietly.

When a consumer joins or leaves, the group must re-deal, and
the two protocols differ in what they cost the innocent:
eager revokes everything from everyone and pauses the whole
group for one member's arrival; incremental revokes only what
changes hands. The first draft of this module then measured
itself into a correction: with hash-based placement the
incremental protocol paused nine times to eager's eight,
because hashing re-homes nearly every partition on every
membership change, and a protocol that only pauses the
affected cannot help when the placement affects everyone. The
re-deal is therefore sticky, surviving members keep their
partitions and only orphans and newcomers' shares move, and
under that placement the drill shows the honest gap, which
is smaller than the brochure: joining the seventh consumer
pauses all seven under eager and five under incremental,
because giving the newcomer four partitions touches four
donors, and the savings are exactly the uninvolved. There
was a third correction on the way here: the first sticky
loop balanced by quota overflow and starved the newcomer at
zero partitions when everyone sat exactly at quota, so the
balance now runs on pairwise imbalance, and the loads prove
it, five each across the group.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class ConsumerGroup:
    protocol: str
    partitions: int
    members: list[str] = field(default_factory=list)
    assignment: dict[int, str] = field(default_factory=dict)
    pauses: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.protocol not in ("eager", "incremental"):
            raise Invalid(
                "the protocol is eager or incremental; eager "
                "survives on the strength of being the default"
            )
        if self.partitions < 1:
            raise Invalid("a group needs partitions to deal")

    def _sticky_ideal(self) -> dict[int, str]:
        if not self.members:
            return {}
        target = {
            partition: holder
            for partition, holder in self.assignment.items()
            if holder in self.members
        }
        loads = {member: 0 for member in self.members}
        for holder in target.values():
            loads[holder] += 1
        while True:
            heavy = max(
                sorted(loads), key=lambda member: loads[member]
            )
            light = min(
                sorted(loads), key=lambda member: loads[member]
            )
            if loads[heavy] < loads[light] + 2:
                break
            moving = max(
                partition
                for partition, holder in target.items()
                if holder == heavy
            )
            target[moving] = light
            loads[heavy] -= 1
            loads[light] += 1
        for partition in range(self.partitions):
            if partition not in target:
                lightest = min(
                    sorted(loads), key=lambda m: loads[m]
                )
                target[partition] = lightest
                loads[lightest] += 1
        return target

    def _apply(self, target: dict[int, str]) -> str:
        moved = [
            partition
            for partition in range(self.partitions)
            if self.assignment.get(partition)
            != target.get(partition)
        ]
        if self.protocol == "eager":
            for member in self.members:
                self.pauses[member] = (
                    self.pauses.get(member, 0) + 1
                )
            note = (
                f"eager: every consumer paused for a re-deal "
                f"that moved {len(moved)} partition(s)"
            )
        else:
            touched = {
                holder
                for partition in moved
                for holder in (
                    self.assignment.get(partition),
                    target.get(partition),
                )
                if holder is not None
                and holder in self.members
            }
            for member in touched:
                self.pauses[member] = (
                    self.pauses.get(member, 0) + 1
                )
            note = (
                f"incremental: {len(touched)} consumer(s) "
                f"paused, the rest never stopped"
            )
        self.assignment = target
        return note

    def join(self, member: str) -> str:
        if member in self.members:
            raise Invalid(f"{member} is already in the group")
        self.members.append(member)
        return self._apply(self._sticky_ideal())

    def leave(self, member: str) -> str:
        if member not in self.members:
            raise Invalid(f"{member} is not in the group")
        self.members.remove(member)
        return self._apply(self._sticky_ideal())

    def pause_bill(self) -> str:
        if not self.pauses:
            return "no rebalances yet; the group is a rumor"
        total = sum(self.pauses.values())
        return (
            f"{self.protocol}: {total} pause event(s) across "
            f"{len(self.pauses)} consumer(s); the columns that "
            "justify the migration ticket"
        )
