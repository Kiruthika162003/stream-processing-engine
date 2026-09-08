"""Session merging: the late event that turns two visits into one.

Session windows are defined by silence, which makes them the
only window kind that can merge: two sessions for a key,
separated by a gap, are two sessions right up until a late
event lands in the silence between them and bridges it,
at which point they were one session all along and the
machinery must agree retroactively. The merger holds sessions
as intervals, extends them when events land inside their gap
reach, and detects the bridge: an event whose reach touches
two sessions collapses them into one, accumulating both
counts, and the collapse is reported with all three
intervals, because a analytics table holding the two old
sessions now holds rows that never happened, and the
downstream correction is only possible if the merge names
what it merged.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SessionSpan:
    start: int
    last: int
    count: int

    def reach(self, gap: int) -> int:
        return self.last + gap

    def label(self) -> str:
        return f"[{self.start}, {self.last}]"


@dataclass
class SessionMerger:
    gap: int
    spans: dict[str, list[SessionSpan]] = field(
        default_factory=dict
    )
    merges: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.gap <= 0:
            raise Invalid("a session gap must be positive")

    def observe(self, key: str, event_time: int) -> str:
        held = self.spans.setdefault(key, [])
        touching = [
            span
            for span in held
            if span.start - self.gap
            <= event_time
            <= span.reach(self.gap)
        ]
        if not touching:
            held.append(
                SessionSpan(
                    start=event_time, last=event_time, count=1
                )
            )
            held.sort(key=lambda span: span.start)
            return f"{key}: new session at {event_time}"
        if len(touching) == 1:
            span = touching[0]
            span.start = min(span.start, event_time)
            span.last = max(span.last, event_time)
            span.count += 1
            return f"{key}: session extends to {span.label()}"
        first, second = sorted(
            touching, key=lambda span: span.start
        )[:2]
        old_labels = f"{first.label()} and {second.label()}"
        first.start = min(first.start, event_time)
        first.last = max(
            first.last, second.last, event_time
        )
        first.count += second.count + 1
        held.remove(second)
        merged_note = (
            f"{key}: the bridge at {event_time} collapses "
            f"{old_labels} into {first.label()}; they were "
            "one session all along, and the table holding "
            "the two old rows now holds rows that never "
            "happened"
        )
        self.merges.append(merged_note)
        return merged_note

    def correction_feed(self) -> str:
        if not self.merges:
            return "no merges; every session stood alone"
        lines = [
            f"{len(self.merges)} retroactive merge(s) for "
            "the downstream correction:"
        ]
        lines.extend(f"  {note}" for note in self.merges)
        return "\n".join(lines)
