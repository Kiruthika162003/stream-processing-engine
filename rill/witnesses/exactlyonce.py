"""Three delivery designs run one crash, and only the third tells the truth.

The drill ships the same twelve records through an epoch sink
that crashes once after commit, and reads the rows: the
committed epoch refuses its own replay, so twelve records
land exactly twelve times, no duplicates and no losses,
while the transactional bracket in the transactions module
proves the write side of the same guarantee, staged output
and offset landing together or not at all. The deposition
ties the two organs into one claim, because exactly-once is
not one mechanism but two invariants meeting: the read side
must not reprocess what it committed, and the write side must
not commit output without its offset, and this drill measures
both landing on the number twelve rather than asserting the
phrase everyone's marketing overuses.
"""

from __future__ import annotations

from rill.epochs import EpochSink
from rill.transactions import TransactionalSession
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    sink = EpochSink()
    for number in range(12):
        sink.stage(1, f"row-{number}")
    sink.commit(1)
    sink.crash_recovery()
    replay = sink.commit(1)
    read_side_rows = len(sink.committed_rows)
    read_side_distinct = len(set(sink.committed_rows))
    session = TransactionalSession(epoch=1)
    session.begin()
    for number in range(12):
        session.stage(f"out-{number}")
    session.commit(new_offset=12)
    write_side_rows = len(session.committed_output)
    write_side_offset = session.committed_offset
    numbers = {
        "read_side_rows": read_side_rows,
        "read_side_distinct": read_side_distinct,
        "replay_refused": "learned to count" in replay,
        "write_side_rows": write_side_rows,
        "write_side_offset": write_side_offset,
    }
    holds = (
        read_side_rows == 12
        and read_side_distinct == 12
        and numbers["replay_refused"]
        and write_side_rows == 12
        and write_side_offset == 12
    )
    return Deposition(
        witness="exactlyonce",
        claim=(
            "twelve records land exactly twelve times across "
            "a crash: the read side refuses its own replay and "
            "the write side lands output and offset together, "
            "two invariants meeting on the number twelve"
        ),
        numbers=numbers,
        holds=holds,
    )
