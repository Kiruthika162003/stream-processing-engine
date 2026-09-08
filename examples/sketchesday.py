"""A sketches day: approximate structures that trade a little accuracy for a lot of memory.

Run with: python -m examples.sketchesday
"""

from __future__ import annotations

from rill.countsketch import CountSketch
from rill.cuckoofilter import CuckooFilter
from rill.minhash import MinHash, similarity
from rill.misragries import MisraGries
from rill.morris import MorrisCounter


def morning_the_similarity():
    left = MinHash(num_hashes=64)
    right = MinHash(num_hashes=64)
    for item in ("a", "b", "c"):
        left.add(item)
        right.add(item)
    print(f"minhash:  identical sets similarity {similarity(left, right)}")


def midday_the_count():
    counter = MorrisCounter()
    for _ in range(3):
        counter.increment(lambda: 0.0)  # force each increment
    print(f"morris:   three forced increments estimate {counter.estimate()}")


def afternoon_the_heavy_hitter():
    gries = MisraGries(k=4)
    for _ in range(400):
        gries.observe("hot")
    for number in range(600):
        gries.observe(f"n{number % 200}")
    print(f"misra:    hot is a candidate: {'hot' in gries.candidates()}")


def dusk_the_frequency():
    sketch = CountSketch(depth=5, width=64)
    sketch.update("lonely", 42)
    print(f"sketch:   a lone key reads back {sketch.estimate('lonely')}")


def night_the_membership():
    cuckoo = CuckooFilter(buckets=64)
    cuckoo.add("member")
    present = cuckoo.contains("member")
    cuckoo.delete("member")
    print(f"cuckoo:   present {present}, after delete {cuckoo.contains('member')}")


def main() -> int:
    morning_the_similarity()
    midday_the_count()
    afternoon_the_heavy_hitter()
    dusk_the_frequency()
    night_the_membership()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
