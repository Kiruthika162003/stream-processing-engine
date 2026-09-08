"""Reservoir sampling: a uniform sample of a stream whose length you never learn.

Sampling k events uniformly from a stream is easy once you know
how many events there are and impossible to do that way on a
stream, whose length is not known until it ends and may not end.
Keeping the first k events is the tempting shortcut and it is
biased: every event after the k-th has zero chance of being
sampled, so the sample is a portrait of the stream's opening and
nothing else. Reservoir sampling holds the uniform guarantee
without the length. The first k events fill the reservoir, and
the i-th event after that displaces a random current member with
probability k over i, which works out so that when the stream
finally stops every event it ever carried sits in the reservoir
with the same probability k over n. This module keeps the
reservoir and takes its random draws from an injected picker, so
the uniformity can be demonstrated on a fixed seed rather than
asserted on faith, and the mechanics can be driven exactly in a
test instead of hoped about.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class Reservoir:
    size: int
    pick: Callable[[int], int]
    _seen: int = 0
    _slots: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.size <= 0:
            raise Invalid("reservoir size must be positive")

    def observe(self, item: str) -> None:
        if self._seen < self.size:
            self._slots.append(item)
            self._seen += 1
            return
        index = self.pick(self._seen)
        if not 0 <= index <= self._seen:
            raise Invalid("picker returned an index outside [0, seen]")
        if index < self.size:
            self._slots[index] = item
        self._seen += 1

    def sample(self) -> list[str]:
        return list(self._slots)

    def seen(self) -> int:
        return self._seen
