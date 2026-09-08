"""A measures day: variance stays honest, a sum stays exact, a tail stops hiding.

Run with: python -m examples.measuresday
"""

from __future__ import annotations

from rill.coordinatedomission import correct, percentile
from rill.ewma import Ewma
from rill.kahan import KahanSum
from rill.usl import peak_workers
from rill.welford import Welford, naive_variance


def morning_the_variance():
    big = 1e9
    data = [big + offset for offset in (1, 2, 3, 4, 5)]
    welford = Welford()
    for sample in data:
        welford.update(sample)
    print(
        f"variance: welford {welford.variance()} vs naive {naive_variance(data)}"
    )


def midday_the_sum():
    kahan = KahanSum()
    for _ in range(1_000_000):
        kahan.add(0.1)
    print(f"sum:      a million tenths total {kahan.total()}")


def afternoon_the_average():
    ewma = Ewma(alpha=0.1)
    ewma.update(100)
    print(
        f"ewma:     raw {round(ewma.raw(), 1)} vs corrected {round(ewma.corrected(), 1)}"
    )


def dusk_the_tail():
    measured = [1] * 990 + [500] + [1] * 9
    naive = percentile(measured, 0.99)
    corrected = percentile(correct(measured, 1), 0.99)
    print(f"tail:     p99 naive {naive} vs corrected {corrected}")


def night_the_peak():
    print(f"scaling:  usl peak at {round(peak_workers(0.03, 0.001))} workers")


def main() -> int:
    morning_the_variance()
    midday_the_sum()
    afternoon_the_average()
    dusk_the_tail()
    night_the_peak()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
