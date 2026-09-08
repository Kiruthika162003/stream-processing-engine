"""Five hundred keys price the moving day, and the plausible scheme loses.

Four workers become five, a 25 percent capacity change, and
the three routing schemes each present their bill for the
same keys: modulo remaps 76 percent, contiguous ranges remap
49, sticky groups remap 21. The middle number is the reason
this witness exists, because the range scheme is the one that
sounds like the fix, keys hash to fixed groups, groups map to
workers, and it still moves half the state; the module's own
docstring recorded that refuted guess and this deposition
keeps the measurement standing guard over it. The floor is
21, close to the 20 the capacity change implies, and the gap
between 21 and 49 is what stickiness is worth on a stage
whose state is expensive to move.
"""

from __future__ import annotations

from rill.rescale import measure_move
from rill.witnesses.deposition import Deposition

KEYS = [f"user-{number}" for number in range(500)]


def run() -> Deposition:
    modulo, ranges, sticky = measure_move(KEYS, 4, 5)
    numbers = {
        "keys": len(KEYS),
        "capacity_change_percent": 25,
        "modulo_moved": modulo.moved,
        "ranges_moved": ranges.moved,
        "sticky_moved": sticky.moved,
        "modulo_percent": 100 * modulo.moved // len(KEYS),
        "ranges_percent": 100 * ranges.moved // len(KEYS),
        "sticky_percent": 100 * sticky.moved // len(KEYS),
    }
    holds = (
        numbers["modulo_moved"] == 384
        and numbers["ranges_moved"] == 246
        and numbers["sticky_moved"] == 106
        and numbers["modulo_percent"] == 76
        and numbers["ranges_percent"] == 49
        and numbers["sticky_percent"] == 21
    )
    return Deposition(
        witness="movebill",
        claim=(
            "a 25 percent capacity change moves 76 percent of "
            "state under modulo, 49 under the plausible range "
            "scheme, and 21 under sticky groups; the middle "
            "bill is the one that sounds like the fix and "
            "still moves half the state"
        ),
        numbers=numbers,
        holds=holds,
    )
