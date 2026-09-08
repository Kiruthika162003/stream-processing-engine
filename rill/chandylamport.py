"""Chandy-Lamport: the snapshot that must also catch the messages in flight.

A consistent snapshot of a distributed pipeline is not just each
operator's state frozen at once, because there is no at-once: a
message can have left its sender and not yet reached its
receiver, in flight on a channel, belonging to neither end's
state. Chandy-Lamport catches those. A process records its own
state the moment it first sees a marker, then sends a marker down
every outgoing channel, and for each incoming channel it records
every message that arrives after its own snapshot until that
channel's marker arrives; those recorded messages are the channel
state, the in-flight records. Skip that recording and the
snapshot loses exactly the messages that were on the wire at
snapshot time, which on recovery are in neither the sender's
saved state, they were already sent, nor the receiver's, they
were not yet processed, so they simply disappear. This module
plays one process's part: it snapshots the local state, records
per-channel in-flight messages between the local snapshot and
each channel's marker, and reports completion once every channel
has closed, so the vanished-message bug is a test rather than a
postmortem.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SnapshotProcess:
    channels: tuple[str, ...]
    _state: str | None = None
    _recording: set[str] = field(default_factory=set)
    _closed: set[str] = field(default_factory=set)
    _channel_state: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.channels:
            raise Invalid("a process needs at least one incoming channel")

    def snapshot(self, state: str) -> None:
        if self._state is not None:
            return
        self._state = state
        self._recording = set(self.channels)
        for channel in self.channels:
            self._channel_state.setdefault(channel, [])

    def receive(self, channel: str, message: str) -> str:
        if channel not in self.channels:
            raise Invalid(f"no channel {channel}")
        if channel in self._recording:
            self._channel_state[channel].append(message)
            return "recorded in flight"
        return "processed normally"

    def marker(self, channel: str) -> None:
        if self._state is None:
            raise Invalid("marker before the local snapshot was taken")
        if channel not in self.channels:
            raise Invalid(f"no channel {channel}")
        self._recording.discard(channel)
        self._closed.add(channel)

    def complete(self) -> bool:
        return self._state is not None and self._closed == set(self.channels)

    def local_state(self) -> str:
        if self._state is None:
            raise Invalid("no snapshot taken")
        return self._state

    def in_flight(self, channel: str) -> list[str]:
        return list(self._channel_state.get(channel, []))
