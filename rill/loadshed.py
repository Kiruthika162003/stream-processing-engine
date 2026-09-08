"""Load shedding: dropping work on purpose to keep the rest alive.

When a stream operator is overwhelmed, doing nothing means
everything slows and eventually nothing completes, so the
disciplined choice is to drop some work deliberately and keep
the rest fast, which is only correct if the dropping is
principled. Shedding by priority keeps the important events
and drops the rest, shedding by sampling keeps a representative
fraction so aggregate metrics stay unbiased even as volume
falls, and the two are for different consumers: an alerting
pipeline needs priority shedding and a metrics pipeline needs
sampling, and shedding the wrong way for the consumer is worse
than not shedding. The load shedder announces every drop as a
counted, categorized loss rather than a silent gap, because
the metrics consumer must know its denominator shrank to
correct for it, and a sampled stream whose sampling rate is
hidden produces numbers that are wrong by exactly the shed
fraction nobody told anyone about.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.content_hash import stable_bucket
from rill.errors import Invalid


@dataclass
class LoadShedder:
    mode: str
    keep_percent: int
    kept: int = 0
    shed: int = 0
    shed_by_reason: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in ("priority", "sampling"):
            raise Invalid(
                "shed by priority or by sampling; the wrong "
                "one for the consumer is worse than not "
                "shedding"
            )
        if not 0 < self.keep_percent <= 100:
            raise Invalid("keep a positive fraction")

    def admit(
        self, event_id: str, priority: str = "normal"
    ) -> bool:
        if self.mode == "priority":
            if priority == "high":
                self.kept += 1
                return True
            if self.keep_percent >= 100:
                self.kept += 1
                return True
            self.shed += 1
            self.shed_by_reason["low-priority"] = (
                self.shed_by_reason.get("low-priority", 0) + 1
            )
            return False
        if stable_bucket(event_id, 100) < self.keep_percent:
            self.kept += 1
            return True
        self.shed += 1
        self.shed_by_reason["sampled-out"] = (
            self.shed_by_reason.get("sampled-out", 0) + 1
        )
        return False

    def denominator_note(self) -> str:
        total = self.kept + self.shed
        if total == 0:
            raise Invalid("nothing offered")
        actual_keep = 100 * self.kept // total
        if self.mode == "sampling":
            return (
                f"kept {self.kept} of {total} ({actual_keep}%); "
                "the metrics consumer must scale by this to "
                "correct, because a hidden shed rate is wrong "
                "by exactly the fraction nobody announced"
            )
        return (
            f"kept {self.kept} of {total} ({actual_keep}%); "
            "priority shed, the alerting consumer keeps every "
            "high-priority event"
        )

    def loss_report(self) -> str:
        lines = [f"{self.shed} event(s) shed, by reason:"]
        for reason, count in sorted(self.shed_by_reason.items()):
            lines.append(f"  {reason}: {count}")
        lines.append(
            "counted and categorized, never a silent gap"
        )
        return "\n".join(lines)
