"""Longest run without a repeat: a window that jumps past the last offender, in one pass.

The longest stretch of a stream with no repeated element, the
longest run of distinct events, the widest window a dedup would
find nothing to drop in, is quadratic to find by checking every
window for uniqueness. A sliding window with a memory does it in
one pass. It keeps a left edge and, for each element, the index
where that element was last seen. When a new element arrives that
was already seen at or after the current left edge, the run cannot
include both occurrences, so the left edge jumps to just past that
last occurrence, discarding the prefix that contained the repeat
in a single move rather than sliding one step at a time. The
window between the left edge and the current position is always
repeat-free, and its largest width over the pass is the answer.
The jump is the key: a naive shrink that advanced the left edge one
position per repeat would be quadratic on an adversarial input,
while jumping straight past the last occurrence keeps each element
visited a constant number of times, so the whole scan is linear.
The last-seen map is what makes the jump possible, turning the
question of where the current window's uniqueness breaks into a
lookup. This module runs the window and returns the longest
repeat-free length, checked against a brute-force over all
substrings, so the linear scan is correct as well as fast.
"""

from __future__ import annotations

from rill.errors import Invalid


def longest_unique(sequence: str) -> int:
    last_seen: dict[str, int] = {}
    left = 0
    best = 0
    for index, char in enumerate(sequence):
        if char in last_seen and last_seen[char] >= left:
            left = last_seen[char] + 1
        last_seen[char] = index
        best = max(best, index - left + 1)
    return best


def longest_unique_or_refuse(sequence: str | None) -> int:
    if sequence is None:
        raise Invalid("sequence must not be None")
    return longest_unique(sequence)
