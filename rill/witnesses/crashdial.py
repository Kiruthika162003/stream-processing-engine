"""One crash, three consumers: the dial's two lies and the bought truth.

The same ten-event tape crashes at offset four under three
consumers. Commit-first loses the crashed event and processes
nine, the quiet lie; process-first replays it and processes
eleven, the loud one; and the third consumer is process-first
wearing a deduper, which refuses the one replay and lands on
exactly ten, the truth, bought with a memory of ten
identities. The deposition exists because the delivery
argument is usually conducted with adjectives and the
occasional whiteboard, and the four numbers in a row, nine,
eleven, ten, and the ten-identity memory bill, are the whole
debate settled in one line each.
"""

from __future__ import annotations

from rill.dedupe import Deduper
from rill.offsets import OffsetConsumer
from rill.witnesses.deposition import Deposition

TAPE_LENGTH = 10
CRASH_AT = 4


def _run_policy(policy: str) -> list[int]:
    consumer = OffsetConsumer(policy=policy)
    for offset in range(CRASH_AT):
        consumer.consume(offset)
    consumer.crash_during(CRASH_AT)
    for offset in range(consumer.resume_from(), TAPE_LENGTH):
        consumer.consume(offset)
    return consumer.processed


def run() -> Deposition:
    quiet = _run_policy("commit-first")
    loud = _run_policy("process-first")
    deduper = Deduper(horizon=1000)
    effectively_once = [
        offset
        for offset in loud
        if deduper.offer(f"evt-{offset}", now=offset)
    ]
    numbers = {
        "tape_length": TAPE_LENGTH,
        "quiet_processed": len(quiet),
        "loud_processed": len(loud),
        "deduped_processed": len(effectively_once),
        "replays_refused": deduper.refused,
        "memory_bill_identities": len(deduper.seen),
    }
    holds = (
        numbers["quiet_processed"] == 9
        and numbers["loud_processed"] == 11
        and numbers["deduped_processed"] == 10
        and numbers["replays_refused"] == 1
        and numbers["memory_bill_identities"] == 10
        and sorted(set(loud)) == list(range(TAPE_LENGTH))
    )
    return Deposition(
        witness="crashdial",
        claim=(
            "nine, eleven, ten: the quiet lie loses one, the "
            "loud lie repeats one, and dedupe on top of the "
            "loud lie lands exactly on the tape, for a memory "
            "bill of ten identities"
        ),
        numbers=numbers,
        holds=holds,
    )
