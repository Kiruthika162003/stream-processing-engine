"""Five values on a billion, one true variance, and the formula that returns zero.

The drill takes five values, one through five, sitting on an
offset of a billion, whose true variance is 2.0, and computes it
two ways. The guess was that the textbook formula, mean of the
squares minus square of the mean, would be a little off from
rounding, maybe a decimal wrong. The measurement is worse than a
little off: it returns exactly 0.0, every significant digit of
the answer cancelled away when float64 subtracted two enormous
nearly-equal terms, a variance of zero for data that plainly
varies. Welford's one-pass method returns 2.0 on the identical
input because it never forms those huge sums, keeping its running
quantities on the scale of the spread. The deposition keeps the
a-little-off guess beside the measured zero, because the surprise
is not that the naive formula loses precision but that it loses
all of it, producing not an inaccurate number but a meaningless
one on exactly the large-offset data timestamps and sensor
readings carry.
"""

from __future__ import annotations

from rill.welford import Welford, naive_variance
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    big = 1e9
    data = [big + offset for offset in (1, 2, 3, 4, 5)]
    welford = Welford()
    for sample in data:
        welford.update(sample)
    welford_var = welford.variance()
    naive_var = naive_variance(data)
    numbers = {
        "true_variance": 2.0,
        "welford_variance": welford_var,
        "naive_variance": naive_var,
        "welford_correct": welford_var == 2.0,
        "naive_cancelled_to_zero": naive_var == 0.0,
    }
    holds = welford_var == 2.0 and naive_var == 0.0
    return Deposition(
        witness="cancellation",
        claim=(
            "on five values one through five offset by a billion, "
            "true variance 2.0, Welford returned 2.0 while the "
            "textbook formula cancelled to exactly 0.0, not "
            "inaccurate but meaningless"
        ),
        numbers=numbers,
        holds=holds,
    )
