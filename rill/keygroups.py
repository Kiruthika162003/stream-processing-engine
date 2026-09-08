"""Key groups: the fixed buckets that let a running job change its width.

Rescale measures which routing scheme moves the least state;
this module builds the mechanism the sticky scheme implies.
State is partitioned not by operator but into a fixed number
of key groups, and rescaling reassigns whole key groups to
operators, so an operator that gains a key group gains its
complete state and one that loses a key group hands it off
whole, no key ever split. The constraint the design enforces
is that the key-group count is the true maximum parallelism,
set once at job creation and never changed, because raising
it later would require repartitioning every key, the exact
all-state-moves migration key groups existed to avoid, and a
max set too low is the ceiling discovered on the day the job
needed to grow past it.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class KeyGroupAssignment:
    key_groups: int
    parallelism: int

    def __post_init__(self) -> None:
        if self.key_groups < 1:
            raise Invalid("a job needs at least one key group")
        if self.parallelism > self.key_groups:
            raise Invalid(
                f"parallelism {self.parallelism} exceeds the "
                f"{self.key_groups} key groups; the key-group "
                "count is the true maximum parallelism, and "
                "this is the ceiling found on growth day"
            )

    def owner_of(self, key_group: int) -> int:
        if not 0 <= key_group < self.key_groups:
            raise Invalid(f"no key group {key_group}")
        span = self.key_groups / self.parallelism
        return min(
            self.parallelism - 1, int(key_group / span)
        )

    def rescale(self, new_parallelism: int) -> str:
        if new_parallelism < 1:
            raise Invalid("a job needs at least one operator")
        if new_parallelism > self.key_groups:
            raise Invalid(
                f"cannot rescale to {new_parallelism}: the "
                f"key-group ceiling is {self.key_groups}, set "
                "once at creation and never raised"
            )
        old = {
            group: self.owner_of(group)
            for group in range(self.key_groups)
        }
        self.parallelism = new_parallelism
        new = {
            group: self.owner_of(group)
            for group in range(self.key_groups)
        }
        moved = sum(
            1 for group in old if old[group] != new[group]
        )
        return (
            f"rescaled to {new_parallelism}: {moved} key "
            f"group(s) reassigned whole, no key split, "
            "state followed its group"
        )
