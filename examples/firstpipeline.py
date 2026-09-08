"""A first pipeline: one disordered tape, from arrival to sealed answers.

Run with: python -m examples.firstpipeline
"""

from __future__ import annotations

from rill.aggregate import WindowedSum
from rill.events import Event, Tape
from rill.lateroom import LateRoom
from rill.operators import Chain, FilterEvents, MapValues
from rill.watermark import BoundedWatermark

READINGS = (
    ("sensor-a", 3, 11), ("sensor-b", 0, 12), ("sensor-a", 5, 14),
    ("sensor-b", 4, 13), ("sensor-a", 2, 22), ("sensor-b", 6, 25),
    ("sensor-a", 1, 12), ("sensor-b", 7, 31),
)


def the_tape() -> Tape:
    tape = Tape()
    for arrival, (key, value, event_time) in enumerate(READINGS):
        tape.record(
            Event(
                key=key, value=value, event_time=event_time,
                arrival=arrival * 5,
            )
        )
    return tape


def main() -> int:
    tape = the_tape()
    print(f"tape:    {tape.report()}")
    clean = Chain(
        stages=[
            FilterEvents(
                name="drop-zeroes",
                keep=lambda event: event.value != 0,
                reason="zero readings are sensor hiccups",
            ),
            MapValues(name="double", fn=lambda value: value * 2),
        ]
    )
    summer = WindowedSum(
        window_size=10,
        watermark=BoundedWatermark(lateness_bound=3),
    )
    room = LateRoom(patience=30, window_size=10)
    for event in tape.in_arrival_order():
        for survivor in clean.process(event):
            notes = summer.feed(survivor)
            for note in notes:
                if "never folded" in note:
                    room.admit(
                        survivor,
                        watermark=summer.watermark.current,
                    )
                    print(f"late:    {survivor.line()}")
                else:
                    print(f"fired:   {note}")
    print(clean.xray())
    print(f"panes:   {summer.ledger()}")
    print(f"room:    {room.histogram()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
