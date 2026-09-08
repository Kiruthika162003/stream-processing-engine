"""Punctuated watermarks: the source that knows beats the heuristic that guesses.

The bounded watermark infers time's progress from event
timestamps and a guessed margin; a punctuating source
declares it, emitting explicit markers, "everything through
T has been sent", because some sources genuinely know, the
batch upstream that finished its hour, the database that
committed its transaction. Declared beats inferred wherever
it is available: no margin to size, no straggler gamble, the
watermark advances exactly when the source says and lateness
becomes the source's broken promise rather than the
pipeline's bad guess. The trust ledger is the counterweight:
every event that arrives behind its source's own punctuation
is a promise broken and is counted against that source,
because a punctuating source that lies is strictly worse
than a heuristic, the heuristic at least knew it was
guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class PunctuatedSource:
    name: str
    declared_through: int = -1
    broken_promises: list[str] = field(default_factory=list)
    events_accepted: int = 0

    def punctuate(self, through: int) -> str:
        if through <= self.declared_through:
            raise Invalid(
                "punctuation moves forward; a retreating "
                "promise is not a promise"
            )
        self.declared_through = through
        return (
            f"{self.name} declares everything through "
            f"{through} sent; no margin to size, no straggler "
            "gamble"
        )

    def event(self, event_time: int) -> str:
        if event_time <= self.declared_through:
            self.broken_promises.append(
                f"event@{event_time} behind the promise of "
                f"{self.declared_through}"
            )
            return (
                f"PROMISE BROKEN: {self.name} sent "
                f"event@{event_time} after declaring "
                f"{self.declared_through}; counted against "
                "the source, not the pipeline"
            )
        self.events_accepted += 1
        return f"event@{event_time} accepted"

    def trust_ledger(self) -> str:
        total = self.events_accepted + len(self.broken_promises)
        if total == 0:
            raise Invalid("no events, no trust to ledger")
        if not self.broken_promises:
            return (
                f"{self.name}: {self.events_accepted} "
                "event(s), every promise kept; declared beats "
                "inferred"
            )
        share = 100 * len(self.broken_promises) // total
        return (
            f"{self.name}: {len(self.broken_promises)} broken "
            f"promise(s) in {total} event(s) ({share}%); a "
            "punctuating source that lies is strictly worse "
            "than a heuristic, which at least knew it was "
            "guessing"
        )
