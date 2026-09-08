"""Checkpoint barriers: aligned snapshots wait for the slowest channel, not the state.

An operator with several input channels checkpoints when a
barrier flows down each one. Aligned checkpointing waits until
the barrier has arrived on every channel before it snapshots, and
a channel whose barrier came early is blocked, its data buffered,
until the last barrier lands. The snapshot is clean and small,
but its start is gated by the slowest channel's barrier lag, so
one backpressured input stalls the whole checkpoint even when the
state to persist is tiny. Unaligned checkpointing snapshots the
moment the first barrier arrives and folds the in-flight buffers
of the not-yet-aligned channels into the snapshot, decoupling
checkpoint duration from alignment at the price of a larger
snapshot that now carries the in-transit records. This module
tracks barrier arrivals per channel and reports, for aligned
mode, how long alignment blocked and how many records piled up
waiting, and for unaligned mode, how many in-flight records the
snapshot had to absorb instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

MODES = ("aligned", "unaligned")


@dataclass
class BarrierTracker:
    channels: int
    mode: str
    _arrived: dict[int, int] = field(default_factory=dict)
    _buffered: int = 0
    _snapshot_taken_at: int | None = None
    _absorbed: int = 0

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise Invalid(f"mode is one of {MODES}")
        if self.channels < 1:
            raise Invalid("need at least one channel")

    def barrier(self, channel: int, at: int) -> None:
        if not 0 <= channel < self.channels:
            raise Invalid(f"no channel {channel}")
        self._arrived[channel] = at
        if self.mode == "unaligned" and self._snapshot_taken_at is None:
            self._snapshot_taken_at = at

    def record_in_flight(self, channel: int, count: int) -> None:
        if channel in self._arrived and self.mode == "aligned":
            self._buffered += count
        elif self.mode == "unaligned" and self._snapshot_taken_at is not None:
            self._absorbed += count

    def aligned(self) -> bool:
        return len(self._arrived) == self.channels

    def alignment_delay(self) -> int:
        if not self.aligned():
            raise Invalid("not every channel has sent its barrier yet")
        return max(self._arrived.values()) - min(self._arrived.values())

    def buffered_during_alignment(self) -> int:
        return self._buffered

    def absorbed_in_flight(self) -> int:
        return self._absorbed
