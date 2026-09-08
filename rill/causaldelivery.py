"""Causal delivery: holding a message until the messages it depends on have arrived.

In a system where nodes broadcast to each other over channels that
can reorder, a message can arrive before the message that caused
it: a reply reaches you before the post it replies to, a
correction before the value it corrects, and acting on it out of
order is a causality violation the user sees as nonsense. Causal
delivery fixes it with vector clocks. Each message carries the
sender's vector clock at send time, which encodes exactly how many
messages from each node the sender had seen, so it is a manifest
of the message's causal dependencies. On receipt, the message is
deliverable only when the receiver has already delivered every
message that manifest names: one more from the sender than the
receiver has seen, and no more from any other node than the
receiver has seen. A message that arrives early, before its
dependencies, is buffered, and each delivery may unblock buffered
messages that were waiting on it, so a cascade of held messages
can flush at once when the missing cause finally lands. The result
is that messages are delivered respecting causality even though
the channels do not, without a global clock or total order, only
the per-message dependency manifest. This module tracks the
delivered clock, buffers the premature, and releases in causal
order, so the reply-before-its-cause anomaly is a buffered wait
rather than a delivered mistake.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class CausalDelivery:
    nodes: tuple[str, ...]
    _clock: dict[str, int] = field(default_factory=dict)
    _buffer: list[tuple[str, dict[str, int], str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.nodes:
            raise Invalid("need at least one node")
        self._clock = dict.fromkeys(self.nodes, 0)

    def _deliverable(self, sender: str, stamp: dict[str, int]) -> bool:
        if stamp.get(sender, 0) != self._clock[sender] + 1:
            return False
        return all(
            stamp.get(other, 0) <= self._clock[other]
            for other in self.nodes
            if other != sender
        )

    def receive(self, sender: str, stamp: dict[str, int], payload: str) -> list[str]:
        if sender not in self._clock:
            raise Invalid(f"unknown sender {sender}")
        self._buffer.append((sender, stamp, payload))
        delivered: list[str] = []
        progressed = True
        while progressed:
            progressed = False
            for entry in list(self._buffer):
                src, clk, msg = entry
                if self._deliverable(src, clk):
                    self._clock[src] += 1
                    delivered.append(msg)
                    self._buffer.remove(entry)
                    progressed = True
        return delivered

    def pending(self) -> int:
        return len(self._buffer)
