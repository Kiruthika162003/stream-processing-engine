"""Checkpoint barriers: a consistent photograph of a system that will not pose.

A running stream cannot be paused for its portrait, so the
barrier flows through the data itself: a marker injected at
the source, and every operator that sees it snapshots its
state at that exact position before processing anything
behind it. The alignment rule is the entire trick: an
operator with two inputs must wait for the barrier on both
before snapshotting, buffering whatever arrives early on the
first channel, because a snapshot taken with one channel
ahead of the other is a photo of a moving car, sharp nowhere.
Recovery restores every operator to the same barrier's
snapshot and replays from there, and the drill proves the
property that justifies all this machinery: the restored run
and an untroubled run end in identical state, which is the
only sentence a checkpoint system owes anyone.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class BarrierOperator:
    name: str
    inputs: int
    state: int = 0
    arrived: set[int] = field(default_factory=set)
    buffered: list[tuple[int, int]] = field(default_factory=list)
    snapshots: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.inputs < 1:
            raise Invalid("an operator needs at least one input")

    def feed(self, channel: int, value: int) -> str:
        if not 0 <= channel < self.inputs:
            raise Invalid(f"{self.name} has no channel {channel}")
        if channel in self.arrived:
            self.buffered.append((channel, value))
            return (
                f"channel {channel} is past the barrier; "
                "buffered, because folding it now would smear "
                "the photograph"
            )
        self.state += value
        return f"folded {value}, state {self.state}"

    def barrier(self, channel: int, barrier_id: int) -> str:
        if channel in self.arrived:
            raise Invalid(
                f"channel {channel} already delivered barrier "
                f"{barrier_id}"
            )
        self.arrived.add(channel)
        if len(self.arrived) < self.inputs:
            return (
                f"barrier on channel {channel}; waiting for "
                f"{self.inputs - len(self.arrived)} more, "
                "buffering the eager"
            )
        self.snapshots[barrier_id] = self.state
        self.arrived.clear()
        replayed = list(self.buffered)
        self.buffered.clear()
        for buffered_channel, value in replayed:
            self.feed(buffered_channel, value)
        return (
            f"aligned: snapshot {barrier_id} = "
            f"{self.snapshots[barrier_id]}, "
            f"{len(replayed)} buffered event(s) released"
        )

    def restore(self, barrier_id: int) -> str:
        if barrier_id not in self.snapshots:
            raise Invalid(
                f"{self.name} holds no snapshot {barrier_id}"
            )
        self.state = self.snapshots[barrier_id]
        self.arrived.clear()
        self.buffered.clear()
        return (
            f"{self.name} restored to snapshot {barrier_id} "
            f"({self.state})"
        )


def recovery_drill() -> str:
    untroubled = BarrierOperator(name="clean", inputs=1)
    crashed = BarrierOperator(name="crashed", inputs=1)
    prefix = [3, 4]
    suffix = [5, 6]
    for operator in (untroubled, crashed):
        for value in prefix:
            operator.feed(0, value)
        operator.barrier(0, barrier_id=1)
    for value in suffix:
        untroubled.feed(0, value)
    crashed.feed(0, suffix[0])
    crashed.restore(barrier_id=1)
    for value in suffix:
        crashed.feed(0, value)
    same = untroubled.state == crashed.state
    return (
        f"untroubled ends at {untroubled.state}, crashed and "
        f"restored ends at {crashed.state}: "
        + (
            "identical, the only sentence a checkpoint system "
            "owes anyone"
            if same
            else "DIVERGED, which is the machinery failing its "
            "one job"
        )
    )
