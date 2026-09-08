"""Bulkhead isolation: one tenant's flood drowns a shared pool, not a partitioned one.

A pool of worker slots shared across tenants has no isolation:
the tenant that grabs every slot, because its dependency stalled
and its calls are all in flight waiting, leaves nothing for
anyone else, and a problem that belongs to one tenant becomes an
outage for all of them. The bulkhead, named for the ship
compartments that keep one breach from flooding the hull, gives
each tenant its own partition of slots so a tenant can exhaust
only its own share. The misbehaving tenant still fails, capped at
its partition, but the blast radius stops there: every other
tenant keeps the capacity reserved for it and never notices. The
trade is utilization, since reserved slots sit idle when their
tenant is quiet where a shared pool would have lent them out, but
that lending is exactly the coupling the bulkhead is paid to
remove. This module runs both a shared pool and a partitioned one
so the difference is a measurement: the same tenant that starves
everyone in the shared pool is contained to its own partition in
the bulkhead, and the others acquire their slots unaffected.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SharedPool:
    total: int
    _in_use: int = 0

    def __post_init__(self) -> None:
        if self.total <= 0:
            raise Invalid("pool must have positive capacity")

    def acquire(self, _tenant: str) -> bool:
        if self._in_use >= self.total:
            return False
        self._in_use += 1
        return True

    def available(self) -> int:
        return self.total - self._in_use


@dataclass
class Bulkhead:
    per_partition: int
    _in_use: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.per_partition <= 0:
            raise Invalid("each partition must have positive capacity")

    def acquire(self, partition: str) -> bool:
        used = self._in_use.get(partition, 0)
        if used >= self.per_partition:
            return False
        self._in_use[partition] = used + 1
        return True

    def release(self, partition: str) -> None:
        used = self._in_use.get(partition, 0)
        if used == 0:
            raise Invalid(f"{partition} holds no slots to release")
        self._in_use[partition] = used - 1

    def available(self, partition: str) -> int:
        return self.per_partition - self._in_use.get(partition, 0)
