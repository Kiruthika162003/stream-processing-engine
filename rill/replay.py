"""Replay: running yesterday through today's code, with both dates showing.

Every stream system eventually reprocesses history, a bug fix
that must repair old aggregates, a new metric that needs a
backfill, and the operation is haunted by two clocks: the
events carry yesterday's event times while the processing
happens today, and any logic that consults the wall clock,
timeouts, "recent" checks, rate limits, will treat historical
events as impossibly old and mangle the backfill silently.
The replay harness therefore runs in declared mode: live mode
may consult the wall clock, replay mode forbids it, and the
forbidden call raises with the module named, because the
wall-clock read that mangles a backfill is never in the code
you are looking at. Output written during replay is tagged
reprocessed with the replay date, so a dashboard showing a
sudden spike in 2023 data can answer the only question that
matters about it: computed when, by which code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Halted, Invalid


@dataclass
class ReplayHarness:
    mode: str
    replay_date: str = ""
    wall_clock_reads: int = 0
    outputs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in ("live", "replay"):
            raise Invalid("mode is live or replay")
        if self.mode == "replay" and not self.replay_date:
            raise Invalid(
                "a replay without its date cannot tag what it "
                "computes"
            )

    def wall_clock(self, caller: str) -> str:
        if self.mode == "replay":
            raise Halted(
                f"{caller} read the wall clock during replay; "
                "this is the call that mangles backfills, and "
                "it is never in the code you are looking at"
            )
        self.wall_clock_reads += 1
        return f"{caller} may consult the wall clock in live mode"

    def emit(self, window_label: str, value: int) -> str:
        if self.mode == "replay":
            line = (
                f"{window_label} = {value} (REPROCESSED "
                f"{self.replay_date})"
            )
        else:
            line = f"{window_label} = {value}"
        self.outputs.append(line)
        return line

    def provenance_answer(self) -> str:
        if self.mode == "live":
            return "computed live, by the code of its day"
        return (
            f"computed on {self.replay_date} by today's code; "
            "the spike in old data has a date and an author"
        )


def backfill_drill() -> str:
    live = ReplayHarness(mode="live")
    live.emit("[2023-04-01)", 100)
    live.wall_clock("timeout-check")
    fixed = ReplayHarness(mode="replay", replay_date="2026-09-08")
    fixed.emit("[2023-04-01)", 140)
    try:
        fixed.wall_clock("timeout-check")
        leaked = True
    except Halted:
        leaked = False
    return (
        f"live wrote {live.outputs[0]!r}; replay wrote "
        f"{fixed.outputs[0]!r}; the timeout check that ran "
        "live was "
        + (
            "allowed to leak into replay"
            if leaked
            else "stopped at the door in replay"
        )
    )
