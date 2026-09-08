"""An analytics day: distinct counts, top keys, decayed trends, and honest tails.

Run with: python -m examples.analyticsday
"""

from __future__ import annotations

from rill.decay import DecayingCounter
from rill.hyperloglog import CardinalityEstimator
from rill.latencyhistogram import LatencyHistogram
from rill.topn import SpaceSaving


def morning_the_distinct_count():
    estimator = CardinalityEstimator()
    for number in range(5000):
        estimator.observe(f"visitor-{number % 3000}")
    print(f"distinct: {estimator.report(error_percent=5)}")


def midday_the_top_pages():
    board = SpaceSaving(capacity=3)
    for _ in range(500):
        board.observe("home")
    for _ in range(300):
        board.observe("search")
    for _ in range(100):
        board.observe("checkout")
    for number in range(50):
        board.observe(f"long-tail-{number}")
    top = board.top(2)
    print(f"top:      {top}")


def afternoon_the_trend():
    hot = DecayingCounter(half_life=10)
    for _ in range(8):
        hot.add(now=0)
    cool = DecayingCounter(half_life=10)
    for _ in range(3):
        cool.add(now=30)
    print(f"trend:    {hot.compare(cool, now=30).split(';')[0]}")


def evening_the_latency():
    histogram = LatencyHistogram()
    for _ in range(980):
        histogram.observe(5)
    for _ in range(20):
        histogram.observe(5000)
    print(f"latency:  {histogram.report().split(';')[0]}")


def main() -> int:
    morning_the_distinct_count()
    midday_the_top_pages()
    afternoon_the_trend()
    evening_the_latency()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
