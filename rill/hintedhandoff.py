"""Hinted handoff: hold a down replica's writes as hints, replay them when it returns.

A write that cannot reach one of its target replicas because the
replica is momentarily down would otherwise leave that replica
behind, under-replicated until some later read repair or
anti-entropy pass notices and fixes it. Hinted handoff keeps the
write instead of dropping it: the coordinator stores a hint, the
value tagged with the replica it was meant for, on a node that is
up, and when the target comes back the hints are replayed to it
in order, so a brief outage costs nothing and the replica catches
up the moment it returns. The catch is that hints are storage,
and a replica that stays down does not stop the writes aimed at
it, so the hints pile up without bound unless capped. Past a hint
cap the coordinator stops hoarding and the returning replica must
be repaired in full rather than replayed, because a hint log the
size of the whole outage is no cheaper than the anti-entropy it
was trying to avoid. This module delivers what it can, stores
hints for what it cannot up to the cap, and replays them on
recovery, so the handoff and its ceiling are both measurable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class HintedHandoff:
    hint_cap: int
    _hints: dict[str, list[str]] = field(default_factory=dict)
    _dropped: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.hint_cap <= 0:
            raise Invalid("hint cap must be positive")

    def write(self, target: str, value: str, reachable: bool) -> str:
        if reachable:
            return "delivered"
        held = self._hints.setdefault(target, [])
        if len(held) >= self.hint_cap:
            self._dropped[target] = self._dropped.get(target, 0) + 1
            return "hint dropped: cap reached, full repair needed on return"
        held.append(value)
        return "hinted"

    def recover(self, target: str) -> list[str]:
        replayed = self._hints.pop(target, [])
        return list(replayed)

    def pending(self, target: str) -> int:
        return len(self._hints.get(target, []))

    def dropped(self, target: str) -> int:
        return self._dropped.get(target, 0)

    def needs_full_repair(self, target: str) -> bool:
        return self._dropped.get(target, 0) > 0
