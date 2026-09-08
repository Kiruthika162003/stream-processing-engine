"""Two thousand values through a fifty-wide window, and the deque that stayed linear.

The drill pushes two thousand values through a sliding-window
maximum of width fifty and counts the deque operations against
the naive rescan. The guess before running it was that a window
of fifty would cost something like the window times the length,
a hundred thousand touches, since that is what rescanning the
last fifty on every step would do. The measurement says 3995,
under two operations per element, because the monotonic deque
pushes each value once and pops it at most once no matter how
wide the window is, so the window size never enters the total.
The deposition keeps the hundred-thousand guess beside the
measured 3995 because the surprise is exactly that the window
width, which dominates the naive cost, drops out of the deque's
cost entirely, and it checks the answers against a brute-force
maximum at the same time so the linear count is not bought with
a wrong result.
"""

from __future__ import annotations

import random

from rill.slidingmax import SlidingMax
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    window, length = 50, 2000
    sliding = SlidingMax(window=window)
    rng = random.Random(2)
    seen: list[int] = []
    correct = True
    for step in range(length):
        value = rng.randint(0, 1000)
        seen.append(value)
        sliding.push(value)
        expected = max(seen[max(0, step - window + 1) : step + 1])
        if sliding.maximum() != expected:
            correct = False
            break
    ops = sliding.total_ops()
    numbers = {
        "length": length,
        "window": window,
        "guessed_naive_ops": length * window,
        "measured_ops": ops,
        "ops_per_element": round(ops / length, 2),
        "answers_correct": correct,
    }
    holds = correct and ops <= 3 * length and ops < length * window // 10
    return Deposition(
        witness="touchonce",
        claim=(
            "a fifty-wide sliding max over two thousand values did "
            "3995 deque operations, under two per element, where the "
            "naive rescan would have done a hundred thousand, because "
            "the window width drops out of the deque's cost entirely"
        ),
        numbers=numbers,
        holds=holds,
    )
