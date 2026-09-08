"""Complex event patterns: finding a sequence in a stream, within a window.

Some questions are about sequences, not single events: a
login followed by a password change followed by a large
transfer within an hour is a fraud pattern no single event
reveals, and complex event processing matches such sequences
as they stream past. The matcher advances a per-key state
machine through the pattern's stages, and the two hazards it
must handle are the ones beginners miss: the pattern has a
time budget, so a sequence that starts but does not complete
within the window must be abandoned, not held forever waiting
for a step that will never come, and a partial match must not
block a fresh start of the same pattern for the same key,
because the second login while the first sequence is pending
is itself the start of a new potential match. The matcher
reports completed patterns and, as usefully, abandoned ones
with the stage they died at, because a pattern that always
dies at stage two is a pattern whose second condition is wrong,
and that diagnosis is invisible without counting the deaths.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class PatternMatcher:
    stages: tuple[str, ...]
    window: int
    partials: dict[str, tuple[int, int]] = field(
        default_factory=dict
    )
    completed: list[str] = field(default_factory=list)
    abandoned_at: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.stages) < 2:
            raise Invalid(
                "a pattern of one stage is just a filter"
            )
        if self.window < 1:
            raise Invalid("a pattern needs a time budget")

    def observe(
        self, key: str, stage: str, now: int
    ) -> str:
        if stage not in self.stages:
            return f"{stage} is not in the pattern; ignored"
        stage_index = self.stages.index(stage)
        if stage_index == 0:
            self.partials[key] = (0, now)
            return f"{key}: pattern started at {stage}"
        held = self.partials.get(key)
        if held is None:
            return f"{key}: {stage} with no started pattern; ignored"
        current_index, started_at = held
        if now - started_at > self.window:
            self.abandoned_at[current_index] = (
                self.abandoned_at.get(current_index, 0) + 1
            )
            del self.partials[key]
            return (
                f"{key}: pattern abandoned, died at stage "
                f"{current_index} past the {self.window} budget"
            )
        if stage_index != current_index + 1:
            return (
                f"{key}: {stage} out of sequence, expected "
                f"{self.stages[current_index + 1]}; ignored"
            )
        if stage_index == len(self.stages) - 1:
            del self.partials[key]
            self.completed.append(key)
            return (
                f"{key}: PATTERN COMPLETE, the whole sequence "
                f"within {self.window}"
            )
        self.partials[key] = (stage_index, started_at)
        return f"{key}: advanced to {stage}"

    def diagnosis(self) -> str:
        if not self.abandoned_at:
            return (
                f"{len(self.completed)} completed, none "
                "abandoned"
            )
        worst_stage = max(
            self.abandoned_at, key=lambda s: self.abandoned_at[s]
        )
        return (
            f"{len(self.completed)} completed, "
            f"{sum(self.abandoned_at.values())} abandoned; most "
            f"die at stage {worst_stage} "
            f"({self.stages[worst_stage]}), so that condition is "
            "likely wrong, a diagnosis invisible without "
            "counting deaths"
        )
