"""Correlating streams: the request and its response, matched by a shared id.

Two streams describe two halves of one story, requests out
and responses back, and correlating them is joining on a
shared correlation id within a timeout, which is where the
interesting failures live: a request with no response is a
timeout or a drop, a response with no request is a bug or a
replay, and a duplicate response is a retry the first response
already answered. The correlator holds pending requests keyed
by id, matches responses against them, and ages out the
unanswered past the timeout into a named orphan list, because
the request that never got its response is exactly the
latency incident someone is being paged about, and calling it
an orphan with its age is more useful than watching a p99
climb. The orphan rate is the health signal: a few orphans
are the tail, a rising orphan rate is a downstream that
stopped answering, and the two get different responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Correlator:
    timeout: int
    pending: dict[str, int] = field(default_factory=dict)
    matched: int = 0
    orphan_responses: list[str] = field(default_factory=list)
    timed_out: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.timeout < 1:
            raise Invalid("correlation needs a timeout")

    def request(self, corr_id: str, now: int) -> str:
        if not corr_id:
            raise Invalid("correlation needs an id")
        if corr_id in self.pending:
            raise Invalid(
                f"{corr_id} already pending; a duplicate "
                "request id makes matching ambiguous"
            )
        self.pending[corr_id] = now
        return f"{corr_id} awaiting its response"

    def response(self, corr_id: str, now: int) -> str:
        sent_at = self.pending.pop(corr_id, None)
        if sent_at is None:
            self.orphan_responses.append(corr_id)
            return (
                f"{corr_id} response with no pending request: "
                "a bug or a replay, not a match"
            )
        self.matched += 1
        return (
            f"{corr_id} matched in {now - sent_at} tick(s)"
        )

    def age_out(self, now: int) -> str:
        orphaned = [
            corr_id
            for corr_id, sent_at in self.pending.items()
            if now - sent_at > self.timeout
        ]
        for corr_id in orphaned:
            del self.pending[corr_id]
            self.timed_out.append(corr_id)
        if not orphaned:
            return "nothing timed out; every request still has hope"
        return (
            f"{len(orphaned)} request(s) orphaned past the "
            f"timeout: {', '.join(orphaned)}; the latency "
            "incident with a name, not a climbing p99"
        )

    def health(self) -> str:
        total = self.matched + len(self.timed_out)
        if total == 0:
            raise Invalid("no completed correlations")
        orphan_rate = 100 * len(self.timed_out) // total
        if orphan_rate >= 20:
            return (
                f"{orphan_rate}% orphan rate: a downstream that "
                "stopped answering, not the tail"
            )
        return (
            f"{orphan_rate}% orphan rate: the tail, "
            f"{self.matched} matched"
        )
