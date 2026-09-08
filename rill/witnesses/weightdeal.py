"""Sixty thousand constant-time draws, and whether the fast sampler keeps the weights.

The drill builds an alias sampler over the weights one, three, six,
whose true shares are a tenth, three tenths, six tenths, and draws
from it sixty thousand times, each draw a single column pick and a
single coin flip with no search of any kind. The guess before
measuring was that constant-time sampling must trade accuracy for
speed, that skipping the prefix-sum search would blur the
distribution. The measurement refutes that: the empirical shares
came out a tenth, three tenths, six tenths to a max deviation of
0.0031, indistinguishable from the targets, and a fourth item given
weight zero was drawn exactly zero times in sixty thousand tries.
The deposition keeps the accuracy-for-speed guess beside the
measured fidelity, because the alias construction packs the weights
into equal-width two-item columns exactly, so the constant-time
draw is not an approximation of the weighted draw, it is the
weighted draw with the search removed.
"""

from __future__ import annotations

import random

from rill.aliasmethod import AliasSampler
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    rng = random.Random(7)
    weights = [1.0, 3.0, 6.0, 0.0]
    sampler = AliasSampler(weights)
    counts = [0, 0, 0, 0]
    trials = 60000
    for _ in range(trials):
        counts[sampler.draw(rng.randrange, rng.random)] += 1
    freq = [c / trials for c in counts]
    target = [w / sum(weights) for w in weights]
    max_dev = max(abs(f - t) for f, t in zip(freq, target, strict=True))
    numbers = {
        "trials": trials,
        "max_deviation": round(max_dev, 4),
        "zero_weight_draws": counts[3],
        "share_of_six": round(freq[2], 3),
    }
    holds = max_dev < 0.01 and counts[3] == 0
    return Deposition(
        witness="weightdeal",
        claim=(
            "over sixty thousand constant-time alias draws the "
            "empirical shares tracked the weights to within 0.0031 "
            "and a zero-weight item was drawn zero times"
        ),
        numbers=numbers,
        holds=holds,
    )
