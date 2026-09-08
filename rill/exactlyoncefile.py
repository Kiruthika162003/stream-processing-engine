"""Exactly-once file output: the rename that makes a partial write invisible.

Writing stream output to files exactly-once faces the same
crash problem as any sink, and files have a clean answer that
databases envy: write to a temporary name and atomically
rename to the final name on commit, so a reader sees the final
file complete or not at all, never half-written. The commit
protocol ties the rename to the checkpoint, a file is finalized
only when its checkpoint commits, so a crash before the
checkpoint leaves an orphan temp file that the next run cleans
up, and a crash after leaves the finalized file with no
duplication because the rename is idempotent, renaming an
already-renamed file is a no-op or a caught error. The trap
the module refuses is finalizing before the checkpoint,
because a file made visible before its checkpoint commits is a
result that survives a rollback the rest of the pipeline
performed, the one inconsistency the whole protocol exists to
prevent, appearing through the file system's back door.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class FileCommitter:
    pending: dict[str, tuple[str, str]] = field(
        default_factory=dict
    )
    finalized: dict[str, str] = field(default_factory=dict)
    orphans_cleaned: int = 0

    def stage(self, final_name: str, content: str) -> str:
        temp = f"{final_name}.tmp"
        self.pending[final_name] = (temp, content)
        return f"{final_name} staged to {temp}, not yet visible"

    def commit_checkpoint(self, final_names: list[str]) -> str:
        finalized_now = []
        for name in final_names:
            if name not in self.pending:
                raise Invalid(
                    f"{name} was never staged; finalizing "
                    "before staging is a visible file with no "
                    "content behind it"
                )
            _temp, content = self.pending.pop(name)
            self.finalized[name] = content
            finalized_now.append(name)
        return (
            f"checkpoint committed: {len(finalized_now)} file(s) "
            "renamed to final, visible only now that the "
            "checkpoint holds"
        )

    def finalize_before_checkpoint(self, name: str) -> str:
        raise Invalid(
            f"{name} finalized before its checkpoint: a file "
            "made visible before commit survives a rollback the "
            "pipeline performed, through the file system's back "
            "door"
        )

    def recover(self) -> str:
        orphans = list(self.pending)
        self.orphans_cleaned += len(orphans)
        self.pending.clear()
        return (
            f"recovery cleaned {len(orphans)} orphan temp "
            f"file(s), kept {len(self.finalized)} finalized; "
            "the crash left no half-written file visible"
        )
