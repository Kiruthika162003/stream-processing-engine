"""Windows: time cut into pieces, each piece knowing its own edges.

A window is half-open on purpose, start inclusive, end
exclusive, because the alternative double-counts every event
that lands exactly on a boundary and the double-count is
discovered in a revenue report, never in a test. Tumbling
windows tile time with no gaps and no overlaps; sliding
windows overlap by design, so one event belongs to several,
and the assignment returns all of them because returning one
would silently drop the others' share; session windows are
different animals entirely, defined by the data rather than
the clock, growing while events keep arriving within a gap of
each other and closing when the silence outlasts the gap. The
assigners are pure functions of event time: they never consult
arrival, because which window an event belongs to is a fact
about when it happened, not about when the network deigned to
deliver it.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class Window:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise Invalid(
                f"a window from {self.start} to {self.end} "
                "contains no time"
            )

    def holds(self, event_time: int) -> bool:
        return self.start <= event_time < self.end

    def label(self) -> str:
        return f"[{self.start}, {self.end})"


def tumbling(event_time: int, size: int) -> Window:
    if size <= 0:
        raise Invalid("a window needs positive size")
    start = (event_time // size) * size
    return Window(start=start, end=start + size)


def sliding(
    event_time: int, size: int, slide: int
) -> list[Window]:
    if size <= 0 or slide <= 0:
        raise Invalid("size and slide must be positive")
    if slide > size:
        raise Invalid(
            "a slide longer than the size leaves gaps that "
            "events fall into silently"
        )
    windows = []
    first_start = ((event_time - size) // slide + 1) * slide
    start = max(0, first_start)
    while start <= event_time:
        windows.append(Window(start=start, end=start + size))
        start += slide
    return windows


@dataclass
class SessionTracker:
    gap: int
    open_start: int | None = None
    open_last: int | None = None
    closed: list[Window] = None

    def __post_init__(self) -> None:
        if self.gap <= 0:
            raise Invalid("a session gap must be positive")
        if self.closed is None:
            self.closed = []

    def observe(self, event_time: int) -> str:
        if self.open_start is None:
            self.open_start = event_time
            self.open_last = event_time
            return f"session opens at {event_time}"
        if event_time - self.open_last <= self.gap:
            self.open_last = max(self.open_last, event_time)
            return (
                f"session extends through {self.open_last}; "
                "the data defines the window, not the clock"
            )
        finished = Window(
            start=self.open_start, end=self.open_last + self.gap
        )
        self.closed.append(finished)
        self.open_start = event_time
        self.open_last = event_time
        return (
            f"silence outlasted the gap: {finished.label()} "
            f"closes and a new session opens at {event_time}"
        )
