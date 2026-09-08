"""Jitter buffer: a playout delay that trades latency for the packets jitter would drop.

A stream of media packets sent at a fixed cadence arrives with
jitter, some early, some late, and playing each the instant it
lands would stutter. A jitter buffer smooths it by holding
packets and playing them on a steady clock keyed to each packet's
send time plus a playout delay, so early packets wait their turn
and the cadence is restored. The delay is the entire trade. A
packet that arrives after its scheduled playout instant is too
late to use and is dropped, leaving a gap, so a small delay drops
every packet whose jitter exceeded it, while a large delay absorbs more
jitter and drops fewer at the cost of adding that delay to every
packet's latency, which for a live call is the difference between
natural and sluggish. There is no delay that both minimizes
latency and drops nothing under real jitter; the buffer is a dial
between them, and sizing it means choosing how much of the jitter
distribution to cover. This module plays a sequence against a
playout clock and counts what arrived in time and what was
dropped as late, so the delay-for-drops trade is a measured pair
rather than a slider tuned by ear.
"""

from __future__ import annotations

from rill.errors import Invalid


def playout(
    arrivals: list[tuple[int, int]], interval: int, playout_delay: int
) -> tuple[int, int]:
    if not arrivals:
        raise Invalid("no packets to play")
    if interval <= 0:
        raise Invalid("interval must be positive")
    if playout_delay < 0:
        raise Invalid("playout delay cannot be negative")
    played = 0
    dropped = 0
    for sequence, arrival in arrivals:
        deadline = sequence * interval + playout_delay
        if arrival <= deadline:
            played += 1
        else:
            dropped += 1
    return played, dropped
