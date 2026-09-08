"""A buffer oscillating at its limit, and the two thresholds that quiet forty flips to one.

The drill drives a bounded buffer up to its pause level and then
oscillates it by one, pop then push, twenty times, first with the
pause and resume levels one apart and then with them five apart.
The guess was that a wider band would cut the control chatter
somewhat. The measurement is starker: the narrow band flips the
producer's paused state 41 times, pausing and resuming on every
push and pop as the buffer hovers at its limit, while the wide
band flips exactly once, pausing at the high watermark and never
draining to the low one, so the same oscillation produces no
further signals. The deposition keeps the somewhat guess beside
the measured 41-to-1 because the surprise is the size of the
difference: a single setpoint does not chatter a little, it
chatters on every operation, and the only cure is a band wide
enough that ordinary jitter cannot cross both edges.
"""

from __future__ import annotations

from rill.hysteresis import HysteresisBuffer
from rill.witnesses.deposition import Deposition


def _flips(low: int, high: int) -> int:
    buffer = HysteresisBuffer(low=low, high=high)
    buffer.push(high)
    for _ in range(20):
        buffer.pop(1)
        buffer.push(1)
    return buffer.flips()


def run() -> Deposition:
    narrow = _flips(9, 10)
    wide = _flips(5, 10)
    numbers = {
        "narrow_band_flips": narrow,
        "wide_band_flips": wide,
        "oscillations": 20,
    }
    holds = narrow == 41 and wide == 1
    return Deposition(
        witness="chatterband",
        claim=(
            "a buffer oscillating by one at its limit flipped the "
            "producer 41 times with a one-wide band and just once "
            "with a five-wide band, so a single setpoint chatters on "
            "every operation and only a band quiets it"
        ),
        numbers=numbers,
        holds=holds,
    )
