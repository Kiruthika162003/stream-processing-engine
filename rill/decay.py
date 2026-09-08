"""Time-decayed counters: recent events weigh more, and the half-life says how much.

A raw count treats an event from an hour ago the same as one
from a second ago, which is wrong for anything trending: the
signal a fraud detector or a hot-topic ranker needs is
weighted toward now. Exponential decay gives every counter a
half-life, the time after which an event's contribution halves,
and the whole design is that this can be computed without
storing every event: keep a value and the time it was last
updated, and on each new event decay the old value by the
elapsed half-lives before adding one. The trap the module
refuses is comparing two decayed counters updated at
different times, because a counter last touched an hour ago is
reporting an hour-stale value that must be decayed to now
before any comparison, and comparing them raw ranks a
freshly-updated small counter below a stale large one that has
actually faded to less. The reading is always decayed to the
query time, never to the last update.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class DecayingCounter:
    half_life: int
    value: float = 0.0
    last_update: int = 0

    def __post_init__(self) -> None:
        if self.half_life < 1:
            raise Invalid("a half-life is at least one tick")

    def _decay_to(self, now: int) -> float:
        if now < self.last_update:
            raise Invalid("a decayed counter cannot read the past")
        elapsed = now - self.last_update
        half_lives = elapsed / self.half_life
        return self.value * (0.5 ** half_lives)

    def add(self, now: int, weight: float = 1.0) -> None:
        self.value = self._decay_to(now) + weight
        self.last_update = now

    def read(self, now: int) -> float:
        return self._decay_to(now)

    def compare(
        self, other: DecayingCounter, now: int
    ) -> str:
        mine = self.read(now)
        theirs = other.read(now)
        if mine > theirs:
            winner = "this"
        elif theirs > mine:
            winner = "the other"
        else:
            return f"tied at {mine:.2f}, both decayed to {now}"
        return (
            f"{winner} counter leads {max(mine, theirs):.2f} to "
            f"{min(mine, theirs):.2f}, both decayed to {now}; "
            "comparing raw would rank a stale large value above "
            "a fresh smaller one that has actually faded less"
        )
