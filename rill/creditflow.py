"""Credit-based flow control: the receiver hands out buffer slots, one per record.

A sender that just writes until the transport blocks head-of-line
blocks every logical channel multiplexed on that transport: one
slow receiver freezes the shared pipe and starves the channels
that had nothing to do with it. Credit-based flow control moves
the bound to the receiver. The receiver announces its free buffer
slots as credit, the sender may send only as many records as it
holds credit for, and each send spends a credit that comes back
only when the receiver drains that record and grants it again.
The sender with no credit stops, but it stops on its own channel,
not on the wire, so a sibling channel with its own credit keeps
flowing past the stalled one. The isolation is the whole point:
backpressure still reaches the source of the slow channel, but it
reaches only that channel. This module tracks per-channel credit,
refuses a send that would overrun the announced buffer, and lets
a stalled channel and a healthy one share a sender without one
starving the other.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid


@dataclass
class CreditChannel:
    capacity: int
    _credit: int = -1
    _in_flight: int = 0

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise Invalid("capacity must be positive")
        if self._credit < 0:
            self._credit = self.capacity

    def can_send(self) -> bool:
        return self._credit > 0

    def send(self) -> None:
        if self._credit <= 0:
            raise Halted("no credit; the receiver's buffer is full")
        self._credit -= 1
        self._in_flight += 1

    def drain(self, count: int) -> None:
        if count > self._in_flight:
            raise Invalid(f"cannot drain {count}; only {self._in_flight} in flight")
        self._in_flight -= count
        self._credit += count

    def credit(self) -> int:
        return self._credit


@dataclass
class CreditMultiplexer:
    capacity: int
    _channels: dict[str, CreditChannel] = field(default_factory=dict)

    def channel(self, name: str) -> CreditChannel:
        if name not in self._channels:
            self._channels[name] = CreditChannel(capacity=self.capacity)
        return self._channels[name]

    def send(self, name: str) -> None:
        self.channel(name).send()

    def sendable(self) -> list[str]:
        return sorted(n for n, c in self._channels.items() if c.can_send())
