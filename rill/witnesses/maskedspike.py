"""Three spikes at a thousand, a bulk near ten, and the sigma test that sees nothing.

The drill builds a series clustered near ten and drops in three
spikes at a thousand, then runs two outlier tests over it. The
guess was that a three-sigma test would obviously flag values a
hundred times the bulk. The measurement is the opposite: the
z-score test flags none of them, because the three spikes drag
the mean up and inflate the standard deviation so far that the
three-sigma band stretches right over the spikes that widened it,
the masking effect. The MAD test, whose center and scale are
medians the spikes cannot move, flags all three. The deposition
keeps the obvious guess beside the measured empty result, because
the surprise is that the reflexive method does not merely
underperform on severe outliers, it reports nothing at all,
declaring a series with values a hundredfold out of range
perfectly clean, while the robust test on the identical data
names every spike.
"""

from __future__ import annotations

from rill.outlier import mad_outliers, zscore_outliers
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    bulk = [10, 11, 9, 10, 12, 8, 11, 10, 9, 10]
    data = [*bulk, 1000, 1000, 1000]
    by_sigma = zscore_outliers(data)
    by_mad = mad_outliers(data)
    numbers = {
        "spikes_present": 3,
        "sigma_flagged": len(by_sigma),
        "mad_flagged": len(by_mad),
        "sigma_masked_all": by_sigma == [],
        "mad_caught_all": by_mad == [1000, 1000, 1000],
    }
    holds = by_sigma == [] and by_mad == [1000, 1000, 1000]
    return Deposition(
        witness="maskedspike",
        claim=(
            "three spikes at a thousand over a bulk near ten were "
            "flagged by none of the three-sigma test, which the "
            "spikes' own inflation of the spread masked, and by all "
            "three of the median-absolute-deviation test"
        ),
        numbers=numbers,
        holds=holds,
    )
