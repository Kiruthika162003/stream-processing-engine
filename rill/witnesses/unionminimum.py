"""A fast input and a slow one prove the union takes the minimum, not the max.

The drill feeds a union two inputs at different speeds, the
fast one racing to watermark 100 while the slow one crawls to
40, and reads the merged watermark: it tracks the slow input
at every step, never the fast one, because a union that took
the maximum would fire windows on data the slow stream still
held. The deposition then marks the slow input idle and
watches the merged watermark jump to the fast input's 100,
confirming the idle-source escape hatch, and marks it active
again to watch the minimum snap back. The three readings,
minimum-while-both-active, freed-by-idle, and pinned-again,
are the entire correctness contract of a union's time
handling, measured rather than asserted.
"""

from __future__ import annotations

from rill.unionstream import UnionStream
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    union = UnionStream()
    union.add_input("fast")
    union.add_input("slow")
    union.advance("fast", 100)
    union.advance("slow", 40)
    both_active = union.merged_watermark()
    union.mark_idle("slow")
    freed_by_idle = union.merged_watermark()
    union.advance("slow", 45)
    pinned_again = union.merged_watermark()
    numbers = {
        "fast_watermark": 100,
        "slow_watermark": 45,
        "both_active_merged": both_active,
        "freed_by_idle_merged": freed_by_idle,
        "pinned_again_merged": pinned_again,
    }
    holds = (
        both_active == 40
        and freed_by_idle == 100
        and pinned_again == 45
    )
    return Deposition(
        witness="unionminimum",
        claim=(
            "the union tracks the slow input at 40 not the "
            "fast at 100, jumps to 100 when the slow input "
            "goes idle, and snaps back to 45 when it speaks "
            "again: the minimum rule and its idle escape "
            "hatch, both measured"
        ),
        numbers=numbers,
        holds=holds,
    )
