"""Boyer-Moore majority: one counter finds the majority, but only if one exists.

Finding the value that occupies more than half a stream, if there
is one, seems to need a count of every distinct value, and the
Boyer-Moore vote does it with a single candidate and a single
counter instead. It holds a candidate and a count, and for each
value it either agrees, incrementing, or disagrees, decrementing,
and when the count hits zero the next value becomes the new
candidate. A true majority survives this because it outnumbers
everything else combined, so the cancellations can never exhaust
it. The catch, and it is the one people forget, is that the
algorithm always produces a candidate whether or not a majority
exists, so on a stream with no majority it returns some value
that means nothing, an artifact of where the cancellations
happened to land. The candidate is therefore a claim, not a
result, and confirming it needs a second pass that counts the
candidate's actual occurrences and checks they exceed half. This
module runs the one-pass vote and the verifying count separately,
so the constant-space find is available and the necessity of the
check is a test: a stream with no majority produces a candidate
the verification correctly rejects.
"""

from __future__ import annotations

from rill.errors import Invalid


def candidate(stream: list[int]) -> int:
    if not stream:
        raise Invalid("empty stream has no candidate")
    chosen = stream[0]
    count = 0
    for value in stream:
        if count == 0:
            chosen = value
        count += 1 if value == chosen else -1
    return chosen


def majority(stream: list[int]) -> int | None:
    if not stream:
        raise Invalid("empty stream")
    chosen = candidate(stream)
    if stream.count(chosen) > len(stream) // 2:
        return chosen
    return None
