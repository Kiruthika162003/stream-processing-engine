"""Determinism auditing: the same input must produce the same output, or replay lies.

Every recovery guarantee in stream processing rests on one
assumption stated rarely and violated often: that reprocessing
the same events produces the same results. If an operator's
output depends on anything but its input and state, the wall
clock, a random number, the iteration order of a hash map, the
response of an external service, then a replay produces
different output than the original run, and every exactly-once
claim built on that replay is false. The auditor runs an
operator twice on identical input and compares, and the value
is in what it flags: a divergence points at a hidden
non-deterministic dependency, and the module classifies the
usual suspects, because knowing that the divergence came from
a time call versus a random seed versus an unordered
iteration sends the fix to a different line. The determinism
contract is not a nice-to-have, it is the load-bearing
assumption, and an operator that cannot pass this audit cannot
honestly claim exactly-once no matter what the framework
promises.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from rill.errors import Invalid

SUSPECTS = {
    "time": "reads the wall clock; inject event time instead",
    "random": "uses an unseeded random; seed from the event",
    "iteration": "depends on hash iteration order; sort first",
    "external": "calls an external service; cache or make it "
    "an input",
}


@dataclass
class DeterminismAudit:
    operator: Callable[[list[str]], str]

    def run_twice(self, events: list[str]) -> tuple[str, str]:
        first = self.operator(list(events))
        second = self.operator(list(events))
        return first, second

    def verdict(self, events: list[str]) -> str:
        first, second = self.run_twice(events)
        if first == second:
            return (
                "deterministic: identical input gave identical "
                "output, so replay tells the truth and "
                "exactly-once can rest on it"
            )
        return (
            "NON-DETERMINISTIC: the same input gave "
            f"{first!r} then {second!r}; every exactly-once "
            "claim built on replaying this operator is false"
        )

    def classify(self, suspect: str) -> str:
        fix = SUSPECTS.get(suspect)
        if fix is None:
            raise Invalid(
                f"{suspect} is not a known non-determinism "
                f"source; the known ones are {sorted(SUSPECTS)}"
            )
        return (
            f"{suspect}: {fix}; the divergence's source picks "
            "the line to fix"
        )
