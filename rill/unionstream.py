"""Union: merging streams into one, and the watermark that must wait for all.

Unioning two streams into one is easy for the events, they
simply interleave, and subtle for time, because the merged
stream's watermark is the minimum of its inputs' watermarks,
not the maximum and not either one alone. A union that took
the faster input's watermark would declare time advanced while
the slower input still had earlier events in flight, firing
windows on incomplete data, so the merged watermark is pinned
to the slowest input exactly as a multi-source operator is
pinned to its slowest partition. The union also inherits the
idle-source problem: one input that goes quiet freezes the
merged watermark unless it is marked idle, so the same
idleness discipline applies. The module exists to make the
minimum rule explicit, because a union implemented as a naive
merge of events without merging watermarks correctly is a
correctness bug that only shows up when the two inputs have
different speeds, which in production they always do.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class UnionStream:
    input_watermarks: dict[str, int] = field(default_factory=dict)
    idle: set[str] = field(default_factory=set)
    merged_history: list[int] = field(default_factory=list)

    def add_input(self, name: str) -> None:
        if name in self.input_watermarks:
            raise Invalid(f"{name} already a union input")
        self.input_watermarks[name] = -1

    def advance(self, name: str, watermark: int) -> str:
        if name not in self.input_watermarks:
            raise Invalid(f"{name} is not a union input")
        if watermark < self.input_watermarks[name]:
            raise Invalid("input watermarks never retreat")
        self.input_watermarks[name] = watermark
        self.idle.discard(name)
        merged = self.merged_watermark()
        self.merged_history.append(merged)
        return (
            f"{name} at {watermark}, merged watermark "
            f"{merged} (the slowest input, not the fastest)"
        )

    def mark_idle(self, name: str) -> str:
        if name not in self.input_watermarks:
            raise Invalid(f"{name} is not a union input")
        self.idle.add(name)
        return (
            f"{name} idle, excused from the minimum so one "
            "quiet input cannot freeze merged time"
        )

    def merged_watermark(self) -> int:
        active = [
            wm
            for name, wm in self.input_watermarks.items()
            if name not in self.idle
        ]
        if not active:
            raise Invalid(
                "every input idle; the union has no opinion "
                "about time"
            )
        return min(active)

    def correctness_note(self) -> str:
        return (
            f"{len(self.input_watermarks)} input(s), "
            f"{len(self.idle)} idle; merged watermark is the "
            "minimum, because taking the faster input would "
            "fire windows on data the slower input still holds"
        )
