"""An algorithms day: the best window, the next high, the median, and a merge.

Run with: python -m examples.algorithmsday
"""

from __future__ import annotations

from rill.kadane import max_subarray
from rill.kwaymerge import merge
from rill.majority import majority
from rill.nextgreater import next_greater_distances
from rill.quickselect import select


def morning_the_best_window():
    deltas = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    total, lo, hi = max_subarray(deltas)
    print(f"window:   best sum {total} over indices {lo} to {hi}")


def midday_the_next_high():
    series = [3, 1, 4, 1, 5]
    print(f"next:     distances {next_greater_distances(series)}")


def afternoon_the_majority():
    votes = [7, 7, 3, 7, 2, 7, 7]
    print(f"majority: {majority(votes)}")


def dusk_the_median():
    data = [9, 3, 7, 1, 5, 8, 2]
    middle = select(data, len(data) // 2)
    print(f"median:   {middle}")


def night_the_merge():
    streams = [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
    print(f"merge:    {merge(streams)}")


def main() -> int:
    morning_the_best_window()
    midday_the_next_high()
    afternoon_the_majority()
    dusk_the_median()
    night_the_merge()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
