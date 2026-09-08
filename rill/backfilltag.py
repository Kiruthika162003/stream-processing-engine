"""Reprocessing tags: the corrected number and the number it replaces, both shown.

When a backfill recomputes a metric, the new value must reach
the same dashboards, reports, and downstream jobs that saw
the old one, and silently overwriting is the trap: a report
already sent, a decision already made on the old number, and
now the history says something different from what everyone
remembers. The tag carries provenance: every reprocessed
value is stamped with a version, the value it superseded, and
the reason, so a consumer can show both, and the alert rule
that would fire on the sudden change instead recognizes the
correction and stays quiet. The append-only rule is the
spine: corrections are new versioned facts, never edits to
old ones, because a metric store you can silently edit is a
metric store nobody can trust in an audit, and the whole
value of stream history is that it is not editable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class MetricHistory:
    metric: str
    versions: dict[int, list[tuple[int, str]]] = field(
        default_factory=dict
    )

    def publish(self, period: int, value: int) -> str:
        chain = self.versions.setdefault(period, [])
        if chain:
            raise Invalid(
                f"{self.metric} period {period} exists; "
                "corrections go through restate, never edit"
            )
        chain.append((value, "original"))
        return f"{self.metric}[{period}] = {value} published"

    def restate(
        self, period: int, value: int, reason: str
    ) -> str:
        chain = self.versions.get(period)
        if chain is None:
            raise Invalid(
                f"{period} was never published; nothing to "
                "restate"
            )
        if not reason.strip():
            raise Invalid(
                "a restatement without a reason is a silent "
                "edit wearing a version number"
            )
        superseded, _ = chain[-1]
        chain.append((value, reason))
        return (
            f"{self.metric}[{period}] restated {superseded} "
            f"-> {value} ({reason}); both shown, so the alert "
            "recognizes a correction instead of firing"
        )

    def read(self, period: int) -> str:
        chain = self.versions.get(period)
        if chain is None:
            raise Invalid(f"{period} has no value")
        value, note = chain[-1]
        if len(chain) == 1:
            return f"{value} (original)"
        original = chain[0][0]
        return (
            f"{value} (RESTATED from {original}: {note}; "
            f"{len(chain)} version(s) on record)"
        )

    def audit_trail(self, period: int) -> str:
        chain = self.versions.get(period)
        if chain is None:
            raise Invalid(f"{period} has no trail")
        lines = [f"{self.metric}[{period}] history:"]
        for version, (value, note) in enumerate(chain):
            lines.append(f"  v{version}: {value} ({note})")
        lines.append(
            "append-only: a metric store you can silently edit "
            "is one nobody can trust in an audit"
        )
        return "\n".join(lines)
