"""Window sizing: resolution is bought in panes, and panes are not free.

Product wants one-minute windows and the pipeline pays in
panes: halve the window and every counter doubles, every
firing doubles, every checkpoint carries twice the state, so
the resolution dial is a cost dial wearing a UX label. The
model prices a configuration honestly: pane count from keys
times windows in flight, firing rate from windows per tick,
state bytes from panes times the per-pane footprint, and the
comparison table for candidate sizes puts the real question
on one page, is the extra resolution worth this specific
bill. The sliding-window multiplier is the line item that
surprises: a sliding window of size S sliding by s holds S/s
panes per key simultaneously, so the smooth dashboard curve
everyone likes is S/s times the tumbling bill, a factor
nobody remembers approving.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

PANE_FOOTPRINT_BYTES = 64


@dataclass(frozen=True)
class WindowConfig:
    label: str
    window_size: int
    slide: int
    active_keys: int
    horizon: int

    def __post_init__(self) -> None:
        if self.window_size < 1 or self.slide < 1:
            raise Invalid("size and slide must be positive")
        if self.slide > self.window_size:
            raise Invalid("a slide past the size leaves gaps")
        if self.active_keys < 1 or self.horizon < 1:
            raise Invalid("keys and horizon must be positive")

    def panes_per_key(self) -> int:
        return self.window_size // self.slide

    def live_panes(self) -> int:
        return self.active_keys * self.panes_per_key()

    def firings_over_horizon(self) -> int:
        return (
            self.horizon // self.slide
        ) * self.active_keys

    def state_bytes(self) -> int:
        return self.live_panes() * PANE_FOOTPRINT_BYTES

    def bill(self) -> str:
        multiplier = self.panes_per_key()
        line = (
            f"{self.label}: {self.live_panes()} live pane(s), "
            f"{self.firings_over_horizon()} firing(s) over the "
            f"horizon, {self.state_bytes()} state byte(s)"
        )
        if multiplier > 1:
            line += (
                f"; the smooth curve costs {multiplier}x the "
                "tumbling bill, a factor nobody remembers "
                "approving"
            )
        return line


def comparison_page(configs: list[WindowConfig]) -> str:
    if len(configs) < 2:
        raise Invalid("a comparison needs candidates")
    lines = [
        "the real question on one page: is the resolution "
        "worth this specific bill"
    ]
    lines.extend(f"  {config.bill()}" for config in configs)
    cheapest = min(configs, key=lambda c: c.state_bytes())
    dearest = max(configs, key=lambda c: c.state_bytes())
    ratio = dearest.state_bytes() / max(
        cheapest.state_bytes(), 1
    )
    lines.append(
        f"{dearest.label} holds {ratio:.0f}x the state of "
        f"{cheapest.label}"
    )
    return "\n".join(lines)
