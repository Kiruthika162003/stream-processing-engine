"""Windowed joins: matching two streams within the same window, symmetrically.

An interval join matches events within a time tolerance; a
windowed join matches events that fall in the same window,
which is a different question with a subtler failure. The
window boundary is a cliff: two events three ticks apart join
under an interval tolerance of five, but if the window edge
falls between them they land in different windows and never
join, so the same two events join or not depending on an
alignment they did not choose. The join makes this explicit
rather than surprising, reporting boundary-straddling near
misses as a named category, because the analyst who sees
fewer joins than expected is usually looking at events split
by a window edge, not at missing data. The symmetry rule is
the correctness spine: a windowed join must produce the same
matches whichever stream is called left, and the module
checks that both orderings agree, since an asymmetric join is
a join that depends on arrival order, which is the bug
windowing was supposed to remove.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid
from rill.windows import tumbling


@dataclass
class WindowedJoin:
    window_size: int
    left: dict[int, list[int]] = field(default_factory=dict)
    right: dict[int, list[int]] = field(default_factory=dict)
    near_misses: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.window_size < 1:
            raise Invalid("a window needs positive size")

    def _window_id(self, event_time: int) -> int:
        return tumbling(event_time, self.window_size).start

    def feed_left(self, event_time: int) -> None:
        self.left.setdefault(
            self._window_id(event_time), []
        ).append(event_time)

    def feed_right(self, event_time: int) -> None:
        self.right.setdefault(
            self._window_id(event_time), []
        ).append(event_time)

    def matches(self) -> list[tuple[int, int]]:
        found = []
        for window_id in sorted(
            set(self.left) & set(self.right)
        ):
            for left_time in self.left[window_id]:
                for right_time in self.right[window_id]:
                    found.append((left_time, right_time))
        return found

    def detect_near_misses(self, tolerance: int) -> str:
        misses = 0
        for left_window, left_times in self.left.items():
            for left_time in left_times:
                for right_window, right_times in (
                    self.right.items()
                ):
                    if left_window == right_window:
                        continue
                    for right_time in right_times:
                        if (
                            abs(left_time - right_time)
                            <= tolerance
                        ):
                            misses += 1
                            self.near_misses.append(
                                f"{left_time} and {right_time} "
                                "split by a window edge"
                            )
        if misses == 0:
            return "no boundary near-misses; the windows align"
        return (
            f"{misses} near-miss(es) split by window edges: "
            "the analyst seeing fewer joins is looking at "
            "these, not at missing data"
        )

    def symmetry_check(self) -> str:
        forward = {tuple(pair) for pair in self.matches()}
        swapped = WindowedJoin(window_size=self.window_size)
        swapped.left = dict(self.right)
        swapped.right = dict(self.left)
        backward = {
            (b, a) for a, b in swapped.matches()
        }
        if forward == backward:
            return (
                "symmetric: the same matches whichever stream "
                "is left, so the join does not depend on "
                "arrival order"
            )
        return "ASYMMETRIC: the join depends on which stream is left"
