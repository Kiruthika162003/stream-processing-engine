"""State backends: memory is fast until the state outgrows it.

Keyed state has to live somewhere, and the choice is a
tradeoff the framework should not make silently: an in-memory
backend is fastest and bounded by RAM, so it works until the
key space grows past memory and then the job dies with an
out-of-memory error that looks like a bug but is a capacity
decision nobody made. A disk-backed backend spills to local
storage, trading access latency for a much larger ceiling,
and the right choice depends on the state size the job will
reach, which is knowable in advance from the key cardinality
and per-key size. The module sizes both and refuses to
recommend memory for a state that will exceed it, because the
memory backend's failure mode is not slowness but death, and
a job sized for memory that grows past it fails at the worst
possible time, under the load that grew the state. The
crossover point is where disk's larger ceiling justifies its
latency, and the module computes it rather than leaving it to
the incident.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

MEMORY_ACCESS_NS = 100
DISK_ACCESS_NS = 10000


@dataclass(frozen=True)
class StateProfile:
    key_cardinality: int
    bytes_per_key: int
    memory_budget_bytes: int

    def __post_init__(self) -> None:
        if self.key_cardinality < 1 or self.bytes_per_key < 1:
            raise Invalid("state needs keys with size")
        if self.memory_budget_bytes < 1:
            raise Invalid("a memory budget is positive")

    def state_size(self) -> int:
        return self.key_cardinality * self.bytes_per_key

    def fits_in_memory(self) -> bool:
        return self.state_size() <= self.memory_budget_bytes

    def recommend(self) -> str:
        size = self.state_size()
        if self.fits_in_memory():
            headroom = self.memory_budget_bytes - size
            return (
                f"memory backend: {size} bytes of state fits "
                f"the {self.memory_budget_bytes} budget with "
                f"{headroom} to spare, fastest access"
            )
        overflow = size - self.memory_budget_bytes
        return (
            f"disk backend required: {size} bytes exceeds the "
            f"{self.memory_budget_bytes} budget by {overflow}; "
            "memory here fails not slowly but fatally, under "
            "the load that grew the state"
        )

    def access_cost_note(self) -> str:
        if self.fits_in_memory():
            return (
                f"memory access {MEMORY_ACCESS_NS}ns per lookup; "
                "the disk alternative would cost "
                f"{DISK_ACCESS_NS}ns for no benefit while the "
                "state fits"
            )
        return (
            f"disk access {DISK_ACCESS_NS}ns per lookup is the "
            f"{DISK_ACCESS_NS // MEMORY_ACCESS_NS}x latency the "
            "larger ceiling costs, and the ceiling is not "
            "optional at this state size"
        )
