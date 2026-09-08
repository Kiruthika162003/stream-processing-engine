"""Fifty timers, one watermark jump, and the herd that arrives at once.

Fifty carts go quiet with deadlines spread across three
ticks, and then one watermark advance matures every single
timer in the same call: the herd is fifty, the average per
advance was meaningless, and the callback capacity that
matters is the herd's size, not the mean's. The deposition
also holds the replacement discipline's numbers: re-arming
the same cart ten times leaves one armed timer and nine
replacements, where the stacking alternative would hold ten
timers and fire nine false alarms, so the two counters,
largest herd and replacements, are the entire capacity and
correctness story of a timer service, and both are numbers
this drill measured rather than sentences someone believed.
"""

from __future__ import annotations

from rill.timers import TimerService
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    storm = TimerService()
    for number in range(50):
        storm.set_timer(f"cart-{number}", 10 + number % 3)
    fired = storm.advance(watermark=100)
    replacer = TimerService()
    for round_number in range(10):
        replacer.set_timer("cart-x", 20 + round_number)
    numbers = {
        "timers_set": 50,
        "herd_size": len(fired),
        "largest_herd": storm.largest_herd,
        "rearms": 10,
        "armed_after_rearms": len(replacer.deadlines),
        "replacements": replacer.replaced,
        "false_alarms_avoided": replacer.replaced,
    }
    holds = (
        numbers["herd_size"] == 50
        and numbers["largest_herd"] == 50
        and numbers["armed_after_rearms"] == 1
        and numbers["replacements"] == 9
    )
    return Deposition(
        witness="herdjump",
        claim=(
            "one watermark advance matured all fifty timers "
            "in a single herd, and ten re-arms left one timer "
            "and nine replacements where stacking would have "
            "fired nine false alarms; capacity is the herd, "
            "correctness is the replacement"
        ),
        numbers=numbers,
        holds=holds,
    )
