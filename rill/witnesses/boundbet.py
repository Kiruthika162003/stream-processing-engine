"""One disordered tape prices the watermark bet at three settings.

The same ten events, disorder measured before the drill
starts, run through the same windowed sum under three
lateness bounds. The prose guessed the tape's disorder at
three and the tape says four; the prose guessed bound zero
would simply pay in refusals, and the measurement is
sharper: its one refusal buys it an extra sealed answer,
two panes fired where the cautious bounds fire one. The
third correction is the best one: bounds three and eight
produce identical rows on this tape, fired one, refused
zero, waiting two, so the extra five ticks of caution
bought nothing at all, and that nothing is the number to
bring to the review comment that says "just be safe and
use a big bound".
"""

from __future__ import annotations

from rill.aggregate import WindowedSum
from rill.events import Event, Tape
from rill.watermark import BoundedWatermark
from rill.witnesses.deposition import Deposition

ARRIVALS = (
    (10, 0), (12, 1), (11, 2), (15, 3), (13, 4),
    (20, 5), (14, 6), (25, 7), (22, 8), (30, 9),
)


def _tape() -> Tape:
    tape = Tape()
    for event_time, arrival in ARRIVALS:
        tape.record(
            Event(
                key="k",
                value=1,
                event_time=event_time,
                arrival=arrival * 10,
            )
        )
    return tape


def _run(bound: int) -> tuple[int, int, int]:
    summer = WindowedSum(
        window_size=10,
        watermark=BoundedWatermark(lateness_bound=bound),
    )
    for event in _tape().in_arrival_order():
        summer.feed(event)
    return (
        len(summer.fired),
        len(summer.refused_late),
        len(summer.panes),
    )


def run() -> Deposition:
    disorder = _tape().disorder()
    by_bound = {bound: _run(bound) for bound in (0, 3, 8)}
    numbers = {
        "tape_disorder": disorder,
        "bound0_fired": by_bound[0][0],
        "bound0_refused": by_bound[0][1],
        "bound0_waiting": by_bound[0][2],
        "bound3_fired": by_bound[3][0],
        "bound3_refused": by_bound[3][1],
        "bound3_waiting": by_bound[3][2],
        "bound8_fired": by_bound[8][0],
        "bound8_refused": by_bound[8][1],
        "bound8_waiting": by_bound[8][2],
    }
    holds = (
        disorder == 4
        and by_bound[0] == (2, 1, 1)
        and by_bound[3] == (1, 0, 2)
        and by_bound[3] == by_bound[8]
    )
    return Deposition(
        witness="boundbet",
        claim=(
            "bound zero's one refusal buys an extra sealed "
            "answer, and bounds three and eight are identical "
            "on this tape: the extra caution bought nothing, "
            "which is the number for the review comment that "
            "says just use a big bound"
        ),
        numbers=numbers,
        holds=holds,
    )
