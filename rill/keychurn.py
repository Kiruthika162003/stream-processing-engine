"""Key churn: the state's future size is written in the keyspace's turnover.

Two streams with the same event rate can need wildly
different state: the one keyed by a stable million users
plateaus, the one keyed by session ids grows forever unless
swept, and the difference is churn, the share of each
window's keys never seen before. The census splits arrivals
into returning and novel per window, and the novel share is
the leading indicator the state-size graph confirms a week
later: high churn means the working set never converges, so
the ttl is load-bearing rather than housekeeping, and low
churn means a bounded key set the state will plateau against.
The verdict names which regime a stream is in, because
provisioning state for a plateauing stream by watching its
first hour over-provisions, and provisioning a churning
stream the same way runs out of memory on day three, and the
only way to tell them apart early is the novel-key share, not
the event rate they happen to share.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class ChurnCensus:
    seen: set[str] = field(default_factory=set)
    windows: list[tuple[int, int]] = field(default_factory=list)

    def observe_window(self, keys: list[str]) -> str:
        if not keys:
            raise Invalid("an empty window teaches no churn")
        novel = sum(1 for key in keys if key not in self.seen)
        returning = len(keys) - novel
        self.seen.update(keys)
        self.windows.append((novel, returning))
        share = 100 * novel // len(keys)
        return (
            f"window: {novel} novel, {returning} returning "
            f"({share}% churn)"
        )

    def novel_share(self) -> float:
        if not self.windows:
            raise Invalid("no windows observed")
        recent = self.windows[-3:]
        novel = sum(n for n, _ in recent)
        total = sum(n + r for n, r in recent)
        return novel / total

    def regime(self) -> str:
        share = self.novel_share()
        if share >= 0.5:
            return (
                f"churning at {share:.0%} novel: the working "
                "set never converges, the ttl is load-bearing, "
                "and provisioning from the first hour runs out "
                "of memory on day three"
            )
        if share <= 0.1:
            return (
                f"plateauing at {share:.0%} novel: a bounded "
                "key set the state will settle against; "
                "provisioning from the first hour over-provisions"
            )
        return (
            f"mixed at {share:.0%} novel: neither regime yet, "
            "and the event rate cannot tell them apart, only "
            "this share can"
        )
