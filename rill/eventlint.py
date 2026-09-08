"""Event lint: the schema police stand at the producer's door, not downstream.

A malformed event caught at publish costs one producer one
retry; the same event caught three stages downstream costs a
poison quarantine, a partial aggregate, and an afternoon of
tracing it back, so the linter runs at the door. The checks
are the unfashionable ones that catch real money: required
fields present, the size budget respected because one team's
debug payload is another team's network bill, and the PII
scan, since a user email in a keyless analytics event is a
compliance incident traveling at stream speed. The verdict
per producer is the enforcement lever: lint failures are
billed to the producer that emitted them, by name, because a
platform that bills malformed events to the pipeline teaches
producers that hygiene is someone else's job.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

SIZE_BUDGET = 1024
PII_MARKERS = ("@", "ssn:", "card:")


@dataclass
class EventLinter:
    required: tuple[str, ...]
    failures: dict[str, list[str]] = field(default_factory=dict)
    passed: int = 0

    def __post_init__(self) -> None:
        if not self.required:
            raise Invalid("a linter with no rules is a doorstop")

    def lint(
        self, producer: str, fields: dict[str, str]
    ) -> str:
        problems = []
        for name in self.required:
            if name not in fields:
                problems.append(f"missing {name}")
        size = sum(
            len(key) + len(value)
            for key, value in fields.items()
        )
        if size > SIZE_BUDGET:
            problems.append(
                f"size {size} over the {SIZE_BUDGET} budget; "
                "one team's debug payload is another team's "
                "network bill"
            )
        for key, value in fields.items():
            if any(marker in value for marker in PII_MARKERS):
                problems.append(
                    f"PII marker in {key}; a compliance "
                    "incident traveling at stream speed"
                )
                break
        if not problems:
            self.passed += 1
            return f"{producer}: clean"
        self.failures.setdefault(producer, []).extend(problems)
        return (
            f"{producer} REFUSED AT THE DOOR: "
            + "; ".join(problems)
        )

    def producer_bill(self) -> str:
        if not self.failures:
            return (
                f"{self.passed} event(s) clean; every "
                "producer paid their own hygiene"
            )
        lines = ["lint failures, billed by name:"]
        for producer in sorted(
            self.failures,
            key=lambda name: -len(self.failures[name]),
        ):
            lines.append(
                f"  {producer}: "
                f"{len(self.failures[producer])} failure(s)"
            )
        lines.append(
            "billing malformed events to the pipeline teaches "
            "producers that hygiene is someone else's job"
        )
        return "\n".join(lines)
