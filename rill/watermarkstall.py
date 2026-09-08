"""Watermark stall detection: the pipeline that is up but no longer moving time.

A stream job can be healthy by every liveness check, workers
responding, no errors logged, and completely stuck, because
the watermark has stopped advancing and no window will ever
fire again. This is the failure liveness checks miss by
design: the process is alive, it is time that has died. The
stall detector watches the watermark's own clock against wall
time, and the distinction it draws is the useful one, a
watermark that is slow because events are sparse is fine, a
watermark that is frozen while events keep arriving is the
stall, so the detector correlates watermark movement with
input rate and only alarms when input is flowing and the
watermark is not. The verdict names the likely cause from the
correlation, an idle source holding the minimum or a stuck
operator, because a stall alarm without a suspect sends the
oncall to read every dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class StallDetector:
    stall_threshold: int
    watermark_history: list[tuple[int, int]] = field(
        default_factory=list
    )
    input_history: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.stall_threshold < 1:
            raise Invalid("the stall threshold must be positive")

    def observe(
        self, wall_time: int, watermark: int, events_in: int
    ) -> None:
        if events_in < 0:
            raise Invalid("event counts are nonnegative")
        self.watermark_history.append((wall_time, watermark))
        self.input_history.append(events_in)

    def verdict(self) -> str:
        if len(self.watermark_history) < 2:
            raise Invalid("a stall needs at least two observations")
        first_wall, first_wm = self.watermark_history[0]
        last_wall, last_wm = self.watermark_history[-1]
        wall_elapsed = last_wall - first_wall
        wm_moved = last_wm - first_wm
        recent_input = sum(self.input_history[-3:])
        if wall_elapsed < self.stall_threshold:
            return "too soon to call a stall"
        if wm_moved > 0:
            return (
                f"healthy: watermark advanced {wm_moved} over "
                f"{wall_elapsed} wall tick(s)"
            )
        if recent_input == 0:
            return (
                f"slow, not stalled: watermark frozen but "
                f"input is {recent_input}; sparse events are "
                "fine, this is not the failure to alarm on"
            )
        return (
            f"STALLED: watermark frozen at {last_wm} for "
            f"{wall_elapsed} wall tick(s) while "
            f"{recent_input} event(s) flowed in; the process "
            "is alive, it is time that has died, likely an "
            "idle source holding the minimum or a stuck "
            "operator"
        )
