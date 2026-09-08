"""Event lineage: which input events produced this output, traced backward.

When an aggregate looks wrong, the question is always the same:
which input events went into it, and lineage answers by
recording, per output, the input event ids that contributed.
The cost is real, one edge per contribution, so lineage is a
sampled or scoped feature, on for the accounts under
investigation and off for the firehose, and the module makes
that scope explicit rather than tracking everything and
apologizing about memory later. The backward query returns the
contributing inputs for an output, and the forward query
returns the outputs an input touched, which is the blast
radius when a single bad input is found: not just which
aggregate it corrupted but every downstream aggregate that
consumed that one, because a bad event's damage is the
transitive closure and repairing only the first hop leaves
the rest wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class LineageGraph:
    scoped_keys: set[str]
    contributions: dict[str, set[str]] = field(
        default_factory=dict
    )
    derived_from: dict[str, set[str]] = field(
        default_factory=dict
    )

    def record(
        self, output_id: str, input_id: str, key: str
    ) -> str:
        if key not in self.scoped_keys:
            return f"{key} out of lineage scope; not tracked"
        self.contributions.setdefault(output_id, set()).add(
            input_id
        )
        self.derived_from.setdefault(input_id, set()).add(
            output_id
        )
        return f"{input_id} -> {output_id} recorded"

    def contributors_of(self, output_id: str) -> list[str]:
        found = self.contributions.get(output_id)
        if found is None:
            raise Invalid(
                f"{output_id} has no lineage; either clean or "
                "out of scope"
            )
        return sorted(found)

    def blast_radius(self, input_id: str) -> str:
        if input_id not in self.derived_from:
            raise Invalid(f"{input_id} touched nothing tracked")
        reached: set[str] = set()
        frontier = [input_id]
        while frontier:
            current = frontier.pop()
            for output_id in self.derived_from.get(current, set()):
                if output_id not in reached:
                    reached.add(output_id)
                    frontier.append(output_id)
        return (
            f"{input_id} reached {len(reached)} output(s): "
            f"{', '.join(sorted(reached))}; the damage is the "
            "transitive closure, and repairing only the first "
            "hop leaves the rest wrong"
        )
