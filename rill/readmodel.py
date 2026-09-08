"""The read model: a view maintained by the stream, honest about its age.

Queries want answers in milliseconds and the stream is the
only writer, so the read model materializes: every event
updates the view, every query reads it directly, and the
architecture's one lie waiting to happen is freshness,
because the view trails the stream by whatever the pipeline's
lag is at that moment. The model therefore stamps itself with
the position it has applied through, and every query answer
carries the staleness, view-at-position against
stream-at-head, in the response, not in a dashboard nobody
correlates, because "balance: 4,200 as of 30 events ago" lets
the caller decide what stale means for them, while a bare
4,200 decides for them, silently, in the direction of
overconfidence. Rebuilds replay the stream from zero and the
model refuses queries mid-rebuild by default, since a view
that answers while half-built is not stale, it is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid


@dataclass
class ReadModel:
    applied_through: int = -1
    balances: dict[str, int] = field(default_factory=dict)
    rebuilding: bool = False

    def apply(self, position: int, key: str, delta: int) -> None:
        if position != self.applied_through + 1:
            raise Invalid(
                f"events apply in order; expected "
                f"{self.applied_through + 1}, got {position}"
            )
        self.balances[key] = (
            self.balances.get(key, 0) + delta
        )
        self.applied_through = position

    def query(self, key: str, stream_head: int) -> str:
        if self.rebuilding:
            raise Halted(
                "the view is mid-rebuild; an answer now would "
                "not be stale, it would be wrong"
            )
        staleness = stream_head - self.applied_through - 1
        balance = self.balances.get(key, 0)
        if staleness <= 0:
            return f"{key}: {balance}, current with the stream"
        return (
            f"{key}: {balance} as of {staleness} event(s) "
            "ago; the caller decides what stale means, "
            "instead of a bare number deciding for them"
        )

    def begin_rebuild(self) -> str:
        self.rebuilding = True
        self.applied_through = -1
        self.balances.clear()
        return "rebuild begins; the view stops answering"

    def finish_rebuild(
        self, replayed: list[tuple[str, int]]
    ) -> str:
        if not self.rebuilding:
            raise Invalid("no rebuild in progress")
        for position, (key, delta) in enumerate(replayed):
            self.apply(position, key, delta)
        self.rebuilding = False
        return (
            f"rebuilt through {self.applied_through} from "
            f"{len(replayed)} event(s); answering again"
        )
