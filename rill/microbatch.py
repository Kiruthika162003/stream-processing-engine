"""Micro-batching: the sink wants crates, the events want to leave now.

Databases and object stores charge per request, so the sink
batches: hold events until the crate is full or the timer
fires, whichever comes first, and the two knobs write the
latency contract nobody reads aloud: an event's worst wait is
the flush interval, so the batch p99 is the timer, not the
traffic, and a team that sets a five-second flush has set a
five-second p99 and should hear themselves say it. The
economics run the other way on throughput: bigger crates
amortize the per-request cost, and the ledger prices both,
requests saved against wait ticks added, on the actual
traffic rather than the brochure's. The flush-on-shutdown
rule closes the classic leak: a batcher that only flushes on
full crates strands the last partial crate at every quiet
period and every deploy, and the strand is always someone's
missing order.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class MicroBatcher:
    crate_size: int
    flush_interval: int
    pending: list[tuple[str, int]] = field(default_factory=list)
    last_flush: int = 0
    crates_shipped: int = 0
    events_shipped: int = 0
    wait_ticks: int = 0

    def __post_init__(self) -> None:
        if self.crate_size < 1 or self.flush_interval < 1:
            raise Invalid("the crate and the timer must be positive")

    def offer(self, event_id: str, now: int) -> str | None:
        self.pending.append((event_id, now))
        if len(self.pending) >= self.crate_size:
            return self._flush(now, reason="full crate")
        if now - self.last_flush >= self.flush_interval:
            return self._flush(now, reason="timer")
        return None

    def _flush(self, now: int, reason: str) -> str:
        count = len(self.pending)
        self.wait_ticks += sum(
            now - arrived for _, arrived in self.pending
        )
        self.pending.clear()
        self.last_flush = now
        self.crates_shipped += 1
        self.events_shipped += count
        return f"crate of {count} shipped ({reason})"

    def shutdown(self, now: int) -> str:
        if not self.pending:
            return "nothing stranded; shutdown clean"
        count = len(self.pending)
        note = self._flush(now, reason="shutdown")
        return (
            f"{note}; a batcher that strands its last partial "
            f"crate loses {count} event(s) at every quiet "
            "period, and the strand is always someone's "
            "missing order"
        )

    def contract(self) -> str:
        if self.events_shipped == 0:
            raise Invalid("no traffic, no contract")
        naive_requests = self.events_shipped
        saved = naive_requests - self.crates_shipped
        mean_wait = self.wait_ticks / self.events_shipped
        return (
            f"{self.crates_shipped} request(s) instead of "
            f"{naive_requests} ({saved} saved), mean wait "
            f"{mean_wait:.1f} tick(s), worst wait bounded by "
            f"the {self.flush_interval}-tick timer; a "
            "five-second flush is a five-second p99, said "
            "aloud"
        )
