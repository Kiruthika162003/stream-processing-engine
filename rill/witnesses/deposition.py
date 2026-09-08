"""Deposition: a witness saw the system run, and these are its numbers.

A witness in this package is a measured drill: it builds a
scenario from the real organs, runs it, and testifies with
numbers rather than adjectives. Each deposition carries the
claim in one sentence, the numbers that back it, and a holds
flag the registry can gate on, because a witness whose story
cannot be checked is a character reference, not deposition.
When a drill's first guess was wrong, the docstring of that
witness keeps the wrong guess beside the measured truth; the
correction is the most trustworthy sentence in the file.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass(frozen=True)
class Deposition:
    witness: str
    claim: str
    numbers: dict = field(default_factory=dict)
    holds: bool = False

    def __post_init__(self) -> None:
        if not self.witness.strip() or not self.claim.strip():
            raise Invalid(
                "deposition needs a witness and a claim; "
                "anonymous assertions are rumors"
            )

    def line(self) -> str:
        state = "HOLDS" if self.holds else "BROKEN"
        return f"[{state}] {self.witness}: {self.claim}"

    def detail(self) -> str:
        lines = [self.line()]
        for name in sorted(self.numbers):
            lines.append(f"    {name} = {self.numbers[name]}")
        return "\n".join(lines)
