"""Ten thousand items into a thousand bins, and the peak that one extra probe halves.

The drill drops ten thousand items into a thousand bins, first
by a single random choice and then by taking the lighter of two
random bins, and reads the maximum load. The guess before the
measurement was that a second probe would shave the peak a little,
maybe a few off the top. The measurement is starker: the peak
falls from 24 to 12, halved, while the average stays 10
throughout, because a single random choice keeps landing on
already-tall piles and forcing an item to lose a race between two
bins makes it very unlikely to keep choosing the tallest. A third
probe reaches only 11, so nearly all the benefit is in the second
choice, the classic diminishing return. The deposition keeps the
modest guess beside the measured halving because the surprise is
how much a single extra comparison per item buys, and it holds
the average fixed to show the whole gain lands on the maximum,
which is the number that decides when a worker falls over.
"""

from __future__ import annotations

import random

from rill.powerof2 import max_load
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    balls, bins = 10000, 1000
    peaks = {}
    for choices in (1, 2, 3):
        rng = random.Random(4)
        peaks[choices] = max_load(balls, bins, choices, rng.randrange)
    numbers = {
        "average": balls // bins,
        "one_choice_peak": peaks[1],
        "two_choice_peak": peaks[2],
        "three_choice_peak": peaks[3],
        "second_probe_saved": peaks[1] - peaks[2],
        "third_probe_saved": peaks[2] - peaks[3],
    }
    holds = (
        peaks[1] == 24
        and peaks[2] == 12
        and peaks[3] == 11
        and (peaks[1] - peaks[2]) > (peaks[2] - peaks[3])
    )
    return Deposition(
        witness="secondprobe",
        claim=(
            "a second random probe halved the peak load from 24 to "
            "12 while the average held at 10, and a third probe "
            "reached only 11, so nearly all the gain is in the "
            "second choice"
        ),
        numbers=numbers,
        holds=holds,
    )
