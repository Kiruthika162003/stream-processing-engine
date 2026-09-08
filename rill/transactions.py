"""Read-process-write: the loop that must land together or not at all.

The canonical streaming transaction spans three logs: consume
from input, transform, produce to output, and commit the
input offset, and every partial landing is a specific lie:
output without the offset commit replays the input and
duplicates the output; offset without the output loses the
transformation entirely. The transactional session brackets
all three: writes are staged, the offset moves with them in
one commit, and an abort rolls the stage back and leaves the
offset where it was, so the retry re-reads the same input and
stages the same output, which is the idempotence the bracket
buys. The zombie fence completes it: a session presumed dead
whose writes arrive after its replacement started must be
refused by epoch, because two sessions writing the same
transform is the duplication the bracket exists to prevent,
arriving through the back door.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid


@dataclass
class TransactionalSession:
    epoch: int
    input_offset: int = 0
    staged: list[str] = field(default_factory=list)
    committed_output: list[str] = field(default_factory=list)
    committed_offset: int = 0
    fenced_epoch: int = 0

    def begin(self) -> str:
        if self.epoch < self.fenced_epoch:
            raise Halted(
                f"epoch {self.epoch} is fenced by "
                f"{self.fenced_epoch}; a zombie's writes are "
                "the duplication arriving through the back "
                "door"
            )
        self.staged.clear()
        return f"session epoch {self.epoch} begins"

    def stage(self, record: str) -> None:
        if not record:
            raise Invalid("staging nothing stages nothing")
        self.staged.append(record)

    def commit(self, new_offset: int) -> str:
        if self.epoch < self.fenced_epoch:
            raise Halted(
                f"epoch {self.epoch} fenced during flight; "
                "refused at commit, which is the fence doing "
                "its one job"
            )
        if new_offset <= self.committed_offset:
            raise Invalid("the offset moves with the writes")
        count = len(self.staged)
        self.committed_output.extend(self.staged)
        self.staged.clear()
        self.committed_offset = new_offset
        return (
            f"{count} record(s) and offset {new_offset} landed "
            "together; no partial lie possible"
        )

    def abort(self) -> str:
        count = len(self.staged)
        self.staged.clear()
        return (
            f"{count} staged record(s) rolled back, offset "
            f"stays at {self.committed_offset}; the retry "
            "re-reads the same input"
        )

    def fence(self, new_epoch: int) -> str:
        if new_epoch <= self.fenced_epoch:
            raise Invalid("fences only rise")
        self.fenced_epoch = new_epoch
        return (
            f"epoch fence raised to {new_epoch}; sessions "
            "below it are zombies now"
        )
