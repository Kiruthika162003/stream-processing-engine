"""Event-time reordering: buffering under the watermark to emit disorder back in order.

Events arrive out of event-time order, and an operator that needs
them sorted, a sequence detector, an ordered sink, a session
builder, cannot simply sort what it has seen, because a later
arrival might belong earlier and it has already emitted past that
point. The watermark is what makes ordered emission safe. Hold
arriving events in a buffer, and each time the watermark advances,
release every buffered event whose event time is at or below the
new watermark, in event-time order, because the watermark is the
promise that nothing earlier than it will still arrive, so those
events can never be preceded by a later arrival. What remains in
the buffer is the events ahead of the watermark, still waiting for
the promise to reach them. The bound on this is the same one every
watermark carries: an event that arrives already behind the
watermark is late, past the point of ordered emission, and is
dropped rather than emitted out of order after the fact. So the
reorder buffer trades a bounded delay, holding events until the
watermark passes them, for output that is sorted by event time
within the lateness the watermark allows. This module buffers,
releases on watermark advance in order, and drops the late, so
the disorder-in ordered-out is a measured sequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class EventTimeSorter:
    _watermark: int = -1
    _buffer: list[tuple[int, str]] = field(default_factory=list)
    _dropped: int = 0

    def add(self, event_time: int, value: str) -> bool:
        if event_time <= self._watermark:
            self._dropped += 1
            return False
        self._buffer.append((event_time, value))
        return True

    def advance(self, watermark: int) -> list[tuple[int, str]]:
        if watermark < self._watermark:
            raise Invalid("watermark went backward")
        self._watermark = watermark
        released = sorted(e for e in self._buffer if e[0] <= watermark)
        self._buffer = [e for e in self._buffer if e[0] > watermark]
        return released

    def buffered(self) -> int:
        return len(self._buffer)

    def dropped(self) -> int:
        return self._dropped
