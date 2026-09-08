"""Interval join: asymmetric time bounds so a payment matches its order, not the reverse.

Joining two streams on time is often stated as a symmetric
tolerance, match events within so many seconds of each other, but
the questions that matter are usually directional. A payment
should match the order it followed, within a window that opens at
the order and extends forward, and a symmetric tolerance gets this
wrong at the edge: it would match a payment to an order that came
slightly after it, a payment for an order not yet placed, which is
nonsense the join should never emit. The interval join fixes it
with an asymmetric bound. A right-side event at time r matches a
left-side event at time l, same key, exactly when r lands in the
window l plus lower to l plus upper, where lower and upper can
both be positive to require the right event strictly after the
left, or span zero to allow either side. Setting lower to zero and
upper to the tolerance captures follows-within, which is the
causal shape order-then-payment, sensor-then-alert, request-then-
response actually have. This module joins the two sides on key and
the asymmetric interval, so the causal matches are produced and
the backward ones a symmetric window would wrongly emit are
excluded by construction.
"""

from __future__ import annotations

from rill.errors import Invalid


def interval_join(
    left: list[tuple[str, int]],
    right: list[tuple[str, int]],
    lower: int,
    upper: int,
) -> list[tuple[str, int, int]]:
    if lower > upper:
        raise Invalid("lower bound must not exceed upper bound")
    by_key: dict[str, list[int]] = {}
    for key, time in left:
        by_key.setdefault(key, []).append(time)
    matches: list[tuple[str, int, int]] = []
    for key, right_time in right:
        for left_time in by_key.get(key, []):
            if left_time + lower <= right_time <= left_time + upper:
                matches.append((key, left_time, right_time))
    return sorted(matches)
