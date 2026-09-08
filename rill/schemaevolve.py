"""Schema evolution in flight: old readers, new writers, and the matrix.

A stream's schema changes while events of every vintage are
still in the log, so compatibility is not a property of a
schema but of a pair: can this reader make sense of that
writer. The registry keeps each version's fields with their
defaults and answers the pair question mechanically: a reader
can consume a newer writer if every field the reader requires
still exists, backward; a reader can consume an older writer
if every field the reader added since carries a default,
forward; and the full matrix is printed before a deploy
because the classic outage is a new writer racing ahead of
old readers on another team's schedule. Removal is the sharp
edge: deleting a field breaks every old reader that requires
it, so removal is two releases by law, first a default makes
the field optional everywhere, then the deletion lands on
readers that no longer care.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class SchemaRegistry:
    versions: dict[int, dict[str, int | None]] = field(
        default_factory=dict
    )

    def publish(
        self, version: int, fields: dict[str, int | None]
    ) -> str:
        if version != len(self.versions) + 1:
            raise Invalid(
                f"versions publish in order; expected "
                f"{len(self.versions) + 1}"
            )
        if version > 1:
            previous = self.versions[version - 1]
            removed = [
                name
                for name in previous
                if name not in fields
                and previous[name] is None
            ]
            if removed:
                raise Invalid(
                    f"removing required field(s) "
                    f"{', '.join(sorted(removed))} breaks "
                    "every old reader; removal is two "
                    "releases by law, default first, delete "
                    "second"
                )
        self.versions[version] = dict(fields)
        return f"schema v{version} published"

    def can_read(
        self, reader_version: int, writer_version: int
    ) -> tuple[bool, str]:
        reader = self.versions.get(reader_version)
        writer = self.versions.get(writer_version)
        if reader is None or writer is None:
            raise Invalid("both versions must be published")
        for name, default in reader.items():
            if name in writer:
                continue
            if default is None:
                return False, (
                    f"reader v{reader_version} requires "
                    f"{name}, writer v{writer_version} does "
                    "not write it, and there is no default "
                    "to fall back on"
                )
        return True, (
            f"reader v{reader_version} handles writer "
            f"v{writer_version}"
        )

    def deploy_matrix(self) -> str:
        if len(self.versions) < 2:
            return "one version; compatibility is trivially true"
        lines = ["the matrix, printed before the deploy:"]
        broken = 0
        for reader in sorted(self.versions):
            for writer in sorted(self.versions):
                ok, why = self.can_read(reader, writer)
                if not ok:
                    broken += 1
                    lines.append(f"  BROKEN {why}")
        if broken == 0:
            lines.append(
                "  every pair reads; deploy in any order"
            )
        else:
            lines.append(
                f"  {broken} broken pair(s): the classic "
                "outage is a new writer racing ahead of old "
                "readers on another team's schedule"
            )
        return "\n".join(lines)
