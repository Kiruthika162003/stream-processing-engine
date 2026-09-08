"""Canary routing: a new operator sees one percent before it sees everything.

Deploying a rewritten operator to the whole stream at once
bets the pipeline on code that passed tests but never met
production traffic; the canary bets one percent instead. A
deterministic slice of keys, chosen by hash so a key's
assignment is stable across restarts, routes to the new
operator while the rest stay on the old, and the outputs are
compared per key on the overlap of keys both versions could
have produced. Promotion is a numbers gate, agreement above a
bar over a minimum sample, and the slice is by key rather
than by event because splitting one key's events across two
operator versions splits its state across two versions, and
a session half-built by each is a bug the canary invented
rather than caught. The disagreement report names keys, not
counts, because the fix lives in the key's specific history.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_bucket
from rill.errors import Invalid

AGREEMENT_BAR = 0.95
MIN_SAMPLE = 10


@dataclass
class CanaryRouter:
    canary_percent: int
    old_output: dict[str, int] = field(default_factory=dict)
    new_output: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 < self.canary_percent <= 50:
            raise Invalid(
                "the canary is a slice, 1 to 50 percent, not "
                "the whole flock"
            )

    def routes_to_canary(self, key: str) -> bool:
        return stable_bucket(key, 100) < self.canary_percent

    def record_old(self, key: str, value: int) -> None:
        self.old_output[key] = value

    def record_new(self, key: str, value: int) -> str:
        if not self.routes_to_canary(key):
            raise Invalid(
                f"{key} is not in the canary slice; splitting "
                "a key across versions splits its state, a bug "
                "the canary would invent"
            )
        self.new_output[key] = value
        return f"{key} routed to the canary"

    def promotion_gate(self) -> str:
        compared = sorted(
            set(self.old_output) & set(self.new_output)
        )
        if len(compared) < MIN_SAMPLE:
            return (
                f"HOLD: {len(compared)} of {MIN_SAMPLE} keys "
                "compared; too small a slice to trust"
            )
        disagreements = [
            key
            for key in compared
            if self.old_output[key] != self.new_output[key]
        ]
        share = 1 - len(disagreements) / len(compared)
        if share < AGREEMENT_BAR:
            named = ", ".join(disagreements[:3])
            return (
                f"HOLD: agreement {share:.0%} under the "
                f"{AGREEMENT_BAR:.0%} bar; the work is keys "
                f"{named}, named because the fix lives in each "
                "key's history"
            )
        return (
            f"PROMOTE: {len(compared)} keys compared, "
            f"agreement {share:.0%}; widen the slice"
        )
