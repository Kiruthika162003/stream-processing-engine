"""Sink contracts: the last mile where exactly-once meets a system that isn't.

A pipeline can guarantee exactly-once internally and still
produce duplicates at the sink, because the external system,
a database, a queue, a file, has its own delivery semantics
and the guarantee only holds if the sink honors the same
contract. There are two honest ways to make a sink
exactly-once and the module names both: an idempotent sink,
where writing the same record twice has the same effect as
writing it once, keyed by a deterministic id, and a
transactional sink, where writes commit atomically with the
stream's offset. A sink that is neither is at-least-once no
matter what the pipeline promises, and the contract check
refuses to claim exactly-once for such a sink, because the
lie is discovered downstream as duplicate rows and traced
back through the one component that was honest about being
at-least-once if only anyone had asked it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

SEMANTICS = ("idempotent", "transactional", "at-least-once")


@dataclass
class SinkContract:
    name: str
    semantics: str
    written: dict[str, str] = field(default_factory=dict)
    duplicate_writes: int = 0

    def __post_init__(self) -> None:
        if self.semantics not in SEMANTICS:
            raise Invalid(
                f"{self.name}: semantics is one of {SEMANTICS}"
            )

    def write(self, idempotency_key: str, value: str) -> str:
        if not idempotency_key:
            raise Invalid(
                "exactly-once sinks need a deterministic key; "
                "a keyless write cannot be deduplicated"
            )
        if idempotency_key in self.written:
            self.duplicate_writes += 1
            if self.semantics == "at-least-once":
                return (
                    f"{idempotency_key} written AGAIN: an "
                    "at-least-once sink cannot suppress the "
                    "duplicate, discovered downstream as a "
                    "duplicate row"
                )
            return (
                f"{idempotency_key} write suppressed: the "
                f"{self.semantics} sink honored the contract"
            )
        self.written[idempotency_key] = value
        return f"{idempotency_key} written"

    def claims_exactly_once(self) -> bool:
        return self.semantics in ("idempotent", "transactional")

    def contract_check(self) -> str:
        if self.claims_exactly_once():
            return (
                f"{self.name}: {self.semantics}, "
                f"{self.duplicate_writes} duplicate(s) "
                "suppressed; exactly-once holds to the last mile"
            )
        return (
            f"{self.name}: at-least-once, cannot claim "
            "exactly-once whatever the pipeline promises; the "
            "honest component nobody asked"
        )
