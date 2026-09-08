"""Gap filling: no data and zero are different facts, and dashboards blur them.

A windowed count that receives nothing emits nothing, and the
dashboard drawing that series connects the dots straight
across the silence, rendering an outage as a calm stretch of
zeroes. The gap filler walks the expected window sequence
against the actual one and labels every hole with the only
honest distinction: a zero means the pipeline ran and counted
nothing, an absence means the pipeline did not speak, and the
second must render as a gap, a null, a gray band, anything
but a number, because the difference between "no sales at
3am" and "no data at 3am" is the difference between a quiet
night and a broken collector, and every oncall who confused
them once carries the scar. Filling policies exist for the
honest cases, zero-fill for counters that genuinely count
nothing, carry-forward for gauges that hold their last value,
and both stamp their fills as synthetic.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid

POLICIES = ("render-gap", "zero-fill", "carry-forward")


@dataclass
class GapFiller:
    window_size: int
    policy: str

    def __post_init__(self) -> None:
        if self.window_size <= 0:
            raise Invalid("windows need size")
        if self.policy not in POLICIES:
            raise Invalid(f"policy is one of {POLICIES}")

    def fill(
        self,
        observed: dict[int, int],
        first_start: int,
        last_start: int,
    ) -> list[str]:
        if last_start < first_start:
            raise Invalid("the range runs backward")
        series = []
        previous: int | None = None
        for start in range(
            first_start,
            last_start + self.window_size,
            self.window_size,
        ):
            if start in observed:
                value = observed[start]
                previous = value
                series.append(f"[{start}): {value}")
            elif self.policy == "zero-fill":
                series.append(
                    f"[{start}): 0 (synthetic; the pipeline "
                    "did not speak and the counter policy "
                    "assumes silence counts nothing)"
                )
            elif self.policy == "carry-forward":
                if previous is None:
                    series.append(
                        f"[{start}): GAP (nothing to carry)"
                    )
                else:
                    series.append(
                        f"[{start}): {previous} (synthetic; "
                        "gauge carried forward)"
                    )
            else:
                series.append(
                    f"[{start}): GAP; no sales at 3am and no "
                    "data at 3am are different facts"
                )
        return series

    def outage_check(
        self, observed: dict[int, int], expected_windows: int
    ) -> str:
        missing = expected_windows - len(observed)
        if missing == 0:
            return "every window spoke; the collector is healthy"
        share = 100 * missing // expected_windows
        if share >= 30:
            return (
                f"{missing} of {expected_windows} window(s) "
                f"silent ({share}%): this is a broken "
                "collector wearing a quiet night's clothes"
            )
        return (
            f"{missing} window(s) silent ({share}%); "
            "plausible quiet, worth one glance"
        )
