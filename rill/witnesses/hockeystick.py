"""Three utilizations, and the wait that goes one, nine, ninety-nine.

The drill reads the mean wait of a simple queue at fifty, ninety,
and ninety-nine percent utilization in units of the service time.
The guess going in treats capacity as linear: ninety percent busy
should wait maybe twice what fifty does, and ninety-nine a little
more again. The measurement is the hockey stick: the wait goes
one, nine, ninety-nine, so the jump from ninety to ninety-nine
percent, nine points of utilization a capacity spreadsheet calls
nearly identical, multiplies the wait elevenfold. The deposition
keeps the linear guess beside the measured one-nine-ninety-nine
because the surprise is where the latency hides: not in the load
you can see but in the last few percent of utilization the plan
counts as available, which is why headroom is the latency budget
and not slack to be reclaimed. The numbers are exact, not
simulated, since the mean wait is utilization over one minus
utilization times the service time, a curve that is nearly flat
and then almost vertical.
"""

from __future__ import annotations

from rill.queueing import mean_wait
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    waits = {util: mean_wait(util, 1) for util in (0.5, 0.9, 0.99)}
    numbers = {
        "wait_at_50pct": round(waits[0.5], 2),
        "wait_at_90pct": round(waits[0.9], 2),
        "wait_at_99pct": round(waits[0.99], 2),
        "ninety_to_ninetynine_multiplier": round(waits[0.99] / waits[0.9], 1),
    }
    holds = (
        round(waits[0.5], 2) == 1.0
        and round(waits[0.9], 2) == 9.0
        and round(waits[0.99], 2) == 99.0
    )
    return Deposition(
        witness="hockeystick",
        claim=(
            "the mean wait went one, nine, ninety-nine service times "
            "at fifty, ninety, and ninety-nine percent utilization, "
            "so nine points of utilization near the top multiplied "
            "the wait elevenfold"
        ),
        numbers=numbers,
        holds=holds,
    )
