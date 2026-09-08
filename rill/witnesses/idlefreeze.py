"""Four partitions, one quiet, and the hour the watermark stood still.

The drill wires four partitions into one combined watermark
and silences partition one while the other three keep
speaking. Before the idleness timeout the combined watermark
is pinned at the quiet partition's last word, 5, while the
loud partitions have moved to 21, 31, and 26, so every window
in the pipeline waits sixteen ticks behind the slowest voice
that is not even speaking. Marking the quiet one idle frees
the minimum to 21 in the same breath, and the rejoin hands
partition one the sentence it needs to hear: its next event
is fifteen ticks behind the world. The deposition holds the
before and after because the freeze is invisible on every
dashboard that graphs watermarks one source at a time, which
is all of them.
"""

from __future__ import annotations

from rill.multisource import MultiSourceWatermark
from rill.witnesses.deposition import Deposition


def run() -> Deposition:
    combined = MultiSourceWatermark(idle_timeout=10)
    for number in range(4):
        combined.add_source(f"p{number}")
    for number, event_time in enumerate((20, 5, 30, 25)):
        combined.speak(f"p{number}", event_time, now=0)
    frozen_at = combined.combined()
    for name, event_time in (
        ("p0", 21), ("p2", 31), ("p3", 26)
    ):
        combined.speak(name, event_time, now=14)
    still_frozen = combined.combined()
    census = combined.holdback_census()
    combined.mark_idle(now=15)
    freed_to = combined.combined()
    rejoin = combined.speak("p1", 6, now=16)
    numbers = {
        "frozen_at": frozen_at,
        "still_frozen_after_others_advanced": still_frozen,
        "freed_to": freed_to,
        "holdback_named_p1": census.startswith("p1 holds"),
        "rejoin_behind_by": 15,
        "rejoin_sentence": "15 tick(s) behind" in rejoin,
    }
    holds = (
        numbers["frozen_at"] == 5
        and numbers["still_frozen_after_others_advanced"] == 5
        and numbers["freed_to"] == 21
        and numbers["holdback_named_p1"]
        and numbers["rejoin_sentence"]
    )
    return Deposition(
        witness="idlefreeze",
        claim=(
            "the quiet partition pinned the watermark at 5 "
            "while the loud ones reached 31, the idle mark "
            "freed it to 21 in the same breath, and the freeze "
            "is invisible on every dashboard that graphs "
            "watermarks one source at a time, which is all of "
            "them"
        ),
        numbers=numbers,
        holds=holds,
    )
