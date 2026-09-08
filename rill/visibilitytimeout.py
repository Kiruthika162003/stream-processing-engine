"""Visibility timeout: a delivered message hides for a while, then reappears if unacked.

A queue that guarantees at-least-once delivery without holding a
lock per consumer uses a visibility timeout. When a consumer
receives a message, the message is not deleted, it is hidden for a
timeout; if the consumer acknowledges within that window the
message is deleted for good, and if it does not, because the
consumer crashed or stalled, the message becomes visible again and
is redelivered to someone else. This is what makes the queue
tolerate a dead consumer without losing the message, and it is
why the delivery is at-least-once and never exactly-once: a
consumer that is merely slow, still processing when the timeout
expires, has its message redelivered and processed a second time,
so the timeout is a bet on how long processing takes. Set it
shorter than the real processing time and healthy consumers get
their in-flight messages yanked back and duplicated; set it far
longer and a genuinely crashed consumer's message sits invisible
and unworked until the long timeout finally elapses. There is no
setting that both recovers fast and never duplicates, which is the
at-least-once queue's defining tension. This module hides a
received message for the timeout, deletes it on ack, and
redelivers it when the timeout lapses unacked, so the duplicate
and the recovery delay are measurable states.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid, Missing


@dataclass
class VisibilityQueue:
    timeout: int
    _available: list[str] = field(default_factory=list)
    _in_flight: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timeout <= 0:
            raise Invalid("timeout must be positive")

    def send(self, message: str) -> None:
        self._available.append(message)

    def receive(self, now: int) -> str:
        self._reappear(now)
        if not self._available:
            raise Missing("no visible messages")
        message = self._available.pop(0)
        self._in_flight[message] = now + self.timeout
        return message

    def ack(self, message: str) -> None:
        if message not in self._in_flight:
            raise Invalid(f"{message} is not in flight")
        del self._in_flight[message]

    def _reappear(self, now: int) -> None:
        expired = [m for m, until in self._in_flight.items() if until <= now]
        for message in expired:
            del self._in_flight[message]
            self._available.append(message)

    def tick(self, now: int) -> None:
        self._reappear(now)

    def available(self) -> int:
        return len(self._available)

    def in_flight(self) -> int:
        return len(self._in_flight)
