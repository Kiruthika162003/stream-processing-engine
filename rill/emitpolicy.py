"""Emit policies: when a stateful operator speaks changes what downstream sees.

A stateful operator holding a running total must decide when
to emit, and the choice shapes the entire downstream contract.
On-change emits every time the value moves, giving downstream
a complete audit trail at the cost of volume; on-interval
emits a heartbeat regardless, so downstream can distinguish a
value that stayed 5 from an operator that died holding 5; and
on-threshold emits only when the value crosses a declared
boundary, cheapest but blind between crossings. The policy is
declared, not defaulted, because the downstream consumer's
correctness depends on it: a consumer computing a time-
weighted average needs on-interval and gets garbage from
on-change, while a consumer reacting to alerts needs
on-threshold and drowns under on-change. The module refuses
to emit without a declared policy, since the operator that
emits on a whim is the one whose downstream nobody can reason
about.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

POLICIES = ("on-change", "on-interval", "on-threshold")


@dataclass
class EmitPolicy:
    policy: str
    interval: int = 0
    threshold: int = 0
    value: int = 0
    last_emit_time: int = -1
    last_emitted_value: int | None = None
    emits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.policy not in POLICIES:
            raise Invalid(
                f"the policy is one of {POLICIES}; an operator "
                "that emits on a whim has a downstream nobody "
                "can reason about"
            )
        if self.policy == "on-interval" and self.interval < 1:
            raise Invalid("on-interval needs an interval")
        if self.policy == "on-threshold" and self.threshold < 1:
            raise Invalid("on-threshold needs a threshold")

    def update(self, new_value: int, now: int) -> str | None:
        old = self.value
        self.value = new_value
        if self.policy == "on-change":
            if new_value != self.last_emitted_value:
                return self._emit(now)
            return None
        if self.policy == "on-interval":
            if (
                self.last_emit_time < 0
                or now - self.last_emit_time >= self.interval
            ):
                return self._emit(now)
            return None
        crossed = (old < self.threshold <= new_value) or (
            new_value < self.threshold <= old
        )
        if crossed:
            return self._emit(now)
        return None

    def _emit(self, now: int) -> str:
        self.last_emit_time = now
        self.last_emitted_value = self.value
        line = f"emit {self.value} at {now} ({self.policy})"
        self.emits.append(line)
        return line

    def downstream_note(self) -> str:
        notes = {
            "on-change": (
                "complete audit trail; a consumer computing a "
                "time-weighted average gets garbage from this"
            ),
            "on-interval": (
                "heartbeat included; downstream distinguishes a "
                "steady value from a dead operator"
            ),
            "on-threshold": (
                "crossings only; blind between them, and a "
                "consumer needing the trail starves"
            ),
        }
        return f"{self.policy}: {notes[self.policy]}"
