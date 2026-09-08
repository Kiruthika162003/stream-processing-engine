"""A night of clickstream: sessions, bridges, the famous page, one unique count.

Run with: python -m examples.clicknight
"""

from __future__ import annotations

from rill.cardinality import LinearCounter
from rill.sessionmerge import SessionMerger
from rill.skewmeter import SkewMeter
from rill.topk import SpaceSaving

CLICKS = (
    ("visitor-1", "/home", 10),
    ("visitor-2", "/home", 11),
    ("visitor-1", "/pricing", 13),
    ("visitor-3", "/home", 14),
    ("visitor-1", "/pricing", 28),
    ("visitor-2", "/home", 31),
    ("visitor-1", "/pricing", 20),
    ("visitor-3", "/docs", 40),
)


def the_sessions():
    merger = SessionMerger(gap=8)
    for visitor, _, event_time in CLICKS:
        merger.observe(visitor, event_time)
    print(f"sessions: {merger.correction_feed().splitlines()[0]}")
    spans = merger.spans["visitor-1"]
    print(f"          visitor-1 ended with {spans[0].label()}")


def the_famous_page():
    sketch = SpaceSaving(capacity=3)
    for _, page, _ in CLICKS:
        sketch.offer(page)
    top = sketch.hitters(top=1)
    print(f"famous:   {top[0]}")


def the_unique_visitors():
    counter = LinearCounter(buckets=64)
    for visitor, _, _ in CLICKS:
        counter.offer(visitor)
    print(f"uniques:  {counter.envelope()}")


def the_skew():
    meter = SkewMeter()
    for offset, (_, _, event_time) in enumerate(CLICKS):
        meter.observe(
            event_time=event_time,
            arrival=event_time + (offset % 3),
        )
    print(f"skew:     {meter.what_if_table([2]).splitlines()[1].strip()}")


def main() -> int:
    the_sessions()
    the_famous_page()
    the_unique_visitors()
    the_skew()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
