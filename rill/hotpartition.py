"""Hot partition splitting: the famous key that one partition cannot outrun.

Partitioning promises parallelism until one key gets so busy
that its partition saturates while its siblings idle, and the
usual advice, add partitions, does nothing, because the hot
key still hashes to exactly one of them. The real fix is
splitting the key's own traffic, appending a small salt to
spread it across sub-partitions, but salting breaks the one
thing partitioning guaranteed, per-key order, so the module
makes the trade explicit: split only keys the operator has
declared order-insensitive, and refuse to split an
order-sensitive key with the reason, because a silent split
of an ordered key is the reordering bug from a different
door. The recombine step is the other half nobody plans:
salted sub-aggregates must merge back, and the merge is only
valid for associative aggregates, the same constraint the
local combiner enforces, stated again here because the split
and the merge are one decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

ASSOCIATIVE = ("sum", "max", "count")


@dataclass
class HotSplitter:
    order_sensitive: set[str]
    fanout: int
    sub_aggregates: dict[str, dict[int, int]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if self.fanout < 2:
            raise Invalid("a split needs at least two sub-partitions")

    def route(self, key: str, event_index: int) -> str:
        if key in self.order_sensitive:
            raise Invalid(
                f"{key} is order-sensitive; splitting it is "
                "the reordering bug from a different door"
            )
        salt = event_index % self.fanout
        return f"{key}#{salt}"

    def accumulate(
        self, key: str, event_index: int, value: int
    ) -> None:
        if key in self.order_sensitive:
            raise Invalid(f"{key} cannot be split")
        salt = event_index % self.fanout
        self.sub_aggregates.setdefault(key, {})
        self.sub_aggregates[key][salt] = (
            self.sub_aggregates[key].get(salt, 0) + value
        )

    def recombine(self, key: str, fold: str) -> int:
        if fold not in ASSOCIATIVE:
            raise Invalid(
                f"{fold} sub-aggregates cannot recombine; the "
                "split and the merge are one decision"
            )
        subs = self.sub_aggregates.get(key)
        if subs is None:
            raise Invalid(f"{key} was never accumulated")
        if fold == "max":
            return max(subs.values())
        return sum(subs.values())

    def balance_report(self, key: str) -> str:
        subs = self.sub_aggregates.get(key)
        if not subs:
            raise Invalid(f"{key} has no sub-partitions")
        spread = max(subs.values()) - min(subs.values())
        return (
            f"{key} spread across {len(subs)} sub-partition(s), "
            f"load spread {spread}; the famous key no longer "
            "rides one partition"
        )
