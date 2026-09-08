"""Circuit breaker: closing on a timer alone reopens the instant traffic returns.

A breaker in front of a flaky sink counts failures while closed
and trips open once they cross a threshold, short-circuiting every
call so the failing sink gets a rest instead of a pile-on. The
naive recovery is a timer: wait a cooldown, then close and let
traffic flow again. That reopens under load, because the moment
the timer fires the breaker slams the still-fragile sink with the
full backlog at once, the first failure trips it straight back
open, and the system oscillates between open and a one-request
closed state, which is the retry storm the breaker existed to
stop. The half-open state fixes it: after the cooldown the
breaker admits a single probe, and only a successful probe closes
the circuit while a failed probe reopens it for another cooldown,
so the sink is tested with one request before it is trusted with
all of them. This module runs the three states, counts failures
against the threshold, and gates each call on the current state.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Halted, Invalid

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    threshold: int
    cooldown: int
    _state: str = CLOSED
    _failures: int = 0
    _opened_at: int = 0

    def __post_init__(self) -> None:
        if self.threshold <= 0 or self.cooldown <= 0:
            raise Invalid("threshold and cooldown must be positive")

    def state(self, now: int) -> str:
        if self._state == OPEN and now - self._opened_at >= self.cooldown:
            self._state = HALF_OPEN
        return self._state

    def allow(self, now: int) -> bool:
        return self.state(now) in (CLOSED, HALF_OPEN)

    def on_success(self, now: int) -> None:
        state = self.state(now)
        if state == OPEN:
            raise Halted("the circuit is open; this call should not have run")
        self._state = CLOSED
        self._failures = 0

    def on_failure(self, now: int) -> None:
        state = self.state(now)
        if state == HALF_OPEN:
            self._trip(now)
            return
        if state == OPEN:
            raise Halted("the circuit is open; this call should not have run")
        self._failures += 1
        if self._failures >= self.threshold:
            self._trip(now)

    def _trip(self, now: int) -> None:
        self._state = OPEN
        self._opened_at = now
        self._failures = 0
