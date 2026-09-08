"""Offsets: when you commit decides which lie you survive.

A consumer's offset is its bookmark, and the crash is the
whole design problem: whatever was processed but not
committed happens again, whatever was committed but not
processed never happens at all. Commit before processing and
a crash loses events, at-most-once, the quiet lie; commit
after processing and a crash replays events, at-least-once,
the loud one. There is no third setting on this dial, only
deduplication built on top, so the consumer here makes the
choice explicit at construction and the crash drill replays
both policies over the same tape and counts the losses and
the duplicates, because teams argue this choice in the
abstract and settle it in one afternoon once the two numbers
are on one page.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

POLICIES = ("commit-first", "process-first")


@dataclass
class OffsetConsumer:
    policy: str
    committed: int = 0
    processed: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.policy not in POLICIES:
            raise Invalid(
                f"the dial has two settings, {POLICIES}; "
                "there is no third, only dedupe on top"
            )

    def consume(self, offset: int) -> None:
        if offset != self.committed:
            raise Invalid(
                f"expected offset {self.committed}, got "
                f"{offset}; consumers read in order or not "
                "at all"
            )
        if self.policy == "commit-first":
            self.committed = offset + 1
            self.processed.append(offset)
        else:
            self.processed.append(offset)
            self.committed = offset + 1

    def crash_during(self, offset: int) -> str:
        if self.policy == "commit-first":
            self.committed = offset + 1
            return (
                f"crashed after committing {offset} and before "
                "processing it; the event never happens, the "
                "quiet lie"
            )
        self.processed.append(offset)
        return (
            f"crashed after processing {offset} and before "
            "committing; the event happens again, the loud lie"
        )

    def resume_from(self) -> int:
        return self.committed


def crash_drill(tape_length: int, crash_at: int) -> str:
    if not 0 <= crash_at < tape_length:
        raise Invalid("the crash must land on the tape")
    quiet = OffsetConsumer(policy="commit-first")
    loud = OffsetConsumer(policy="process-first")
    for consumer in (quiet, loud):
        for offset in range(crash_at):
            consumer.consume(offset)
        consumer.crash_during(crash_at)
        for offset in range(consumer.resume_from(), tape_length):
            consumer.consume(offset)
    lost = tape_length - len(quiet.processed)
    duplicated = len(loud.processed) - tape_length
    seen_once_quiet = len(set(quiet.processed))
    return (
        f"one tape, one crash at {crash_at}: commit-first "
        f"processed {seen_once_quiet} of {tape_length} and "
        f"lost {lost}; process-first processed everything "
        f"and repeated {duplicated}; the two numbers that end "
        "the abstract argument"
    )
