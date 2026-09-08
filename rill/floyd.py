"""Floyd's tortoise and hare: finding a loop in a chain without remembering where you've been.

A chain of states where each points to a next, a retry that
reschedules itself, a pointer structure, a sequence generator, can
close into a loop, and detecting that loop the obvious way keeps a
set of everything visited and watches for a repeat, which costs
memory proportional to the chain. Floyd's cycle detection does it
in constant space with two walkers. A slow tortoise advances one
step at a time and a fast hare two, and if the chain is a straight
line the hare runs off the end and there is no cycle, but if the
chain loops the hare, going twice as fast, laps the tortoise and
the two land on the same node, which can only happen inside a
cycle. That meeting proves a loop with no memory of the path.
Finding where the loop begins takes one more insight: reset one
walker to the start and advance both one step at a time, and they
meet at the loop's entrance, because the distance from the start
to the entrance equals the distance from the meeting point around
to the entrance. This module detects the cycle, finds its start,
and measures its length, all in constant space, so the loop that a
visited-set would spend linear memory to catch is caught with two
pointers.
"""

from __future__ import annotations

from collections.abc import Callable

from rill.errors import Invalid


def has_cycle(successor: Callable[[str], str | None], start: str) -> bool:
    slow: str | None = start
    fast: str | None = start
    while fast is not None:
        slow = successor(slow)
        fast = successor(fast)
        if fast is not None:
            fast = successor(fast)
        if slow is not None and slow == fast:
            return True
    return False


def cycle_start(successor: Callable[[str], str | None], start: str) -> str:
    slow: str | None = start
    fast: str | None = start
    while fast is not None:
        slow = successor(slow)
        fast = successor(fast)
        fast = successor(fast) if fast is not None else None
        if slow is not None and slow == fast:
            break
    else:
        raise Invalid("no cycle to find the start of")
    if fast is None:
        raise Invalid("no cycle to find the start of")
    finder: str | None = start
    while finder != slow:
        finder = successor(finder)
        slow = successor(slow)
    return finder


def cycle_length(successor: Callable[[str], str | None], start: str) -> int:
    entrance = cycle_start(successor, start)
    length = 1
    cursor = successor(entrance)
    while cursor != entrance:
        cursor = successor(cursor)
        length += 1
    return length
