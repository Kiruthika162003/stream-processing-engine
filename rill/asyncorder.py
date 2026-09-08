"""Async external calls: ordered emission buys input order with head-of-line stalls.

An operator that makes one async call per event, a lookup or an
enrichment against an outside service, gets its answers back in
the order the service finishes them, which is not the order the
events arrived. Two emission modes make opposite trades.
Unordered emission ships each answer the moment it lands, so a
fast call behind a slow one overtakes it and the output stream
is reordered relative to the input. Ordered emission holds every
completed answer in a buffer and releases it only once every
earlier event has also completed, so the output order matches
the input at the cost of head-of-line blocking: one slow call at
the front of the buffer pins every finished answer behind it,
and the buffer swells to the count of events in flight while that
one call drags. The tell that you picked ordered mode under a
heavy-tailed latency is a buffer that grows with the tail, not
with the throughput.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

MODES = ("ordered", "unordered")


@dataclass
class AsyncEmitter:
    mode: str
    _next_in: int = 0
    _next_out: int = 0
    _ready: dict[int, str] = field(default_factory=dict)
    _high_water: int = 0

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise Invalid(f"mode is one of {MODES}, not {self.mode!r}")

    def submit(self, _value: str) -> int:
        token = self._next_in
        self._next_in += 1
        return token

    def complete(self, token: str, answer: str) -> list[str]:
        if not 0 <= token < self._next_in:
            raise Invalid(f"token {token} was never submitted")
        if self.mode == "unordered":
            return [answer]
        self._ready[token] = answer
        depth = len(self._ready)
        self._high_water = max(self._high_water, depth)
        return self._drain()

    def _drain(self) -> list[str]:
        released: list[str] = []
        while self._next_out in self._ready:
            released.append(self._ready.pop(self._next_out))
            self._next_out += 1
        return released

    def buffered(self) -> int:
        return len(self._ready)

    def peak_buffer(self) -> int:
        return self._high_water
