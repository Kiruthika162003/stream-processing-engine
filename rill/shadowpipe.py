"""The shadow pipeline: version two audits itself against version one, live.

Rewriting a pipeline is easy; proving the rewrite is the
work, and the shadow run does the proving in production
without the risk: both versions consume the same stream, only
version one's output is served, and every window both emit is
compared. The disagreement triage is the streaming twist on
an old idea: a differing value on the same window is a logic
change to explain, a window only the old version emits is
usually the new version's watermark running behind, and a
window only the new version emits is usually early firing,
so each species points at a different part of the rewrite.
Promotion is a numbers gate, agreement over a quota of
windows with every disagreement explained or fixed, and the
cutover memo writes itself from the ledger, which beats the
alternative memo, the one written after serving wrong numbers
for a week.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PROMOTION_QUOTA = 20
AGREEMENT_BAR = 0.95


@dataclass
class ShadowRun:
    served: dict[str, int] = field(default_factory=dict)
    shadowed: dict[str, int] = field(default_factory=dict)
    explained: set[str] = field(default_factory=set)

    def emit_old(self, window: str, value: int) -> None:
        self.served[window] = value

    def emit_new(self, window: str, value: int) -> None:
        self.shadowed[window] = value

    def triage(self) -> dict[str, list[str]]:
        differing = sorted(
            window
            for window in self.served
            if window in self.shadowed
            and self.served[window] != self.shadowed[window]
        )
        old_only = sorted(
            set(self.served) - set(self.shadowed)
        )
        new_only = sorted(
            set(self.shadowed) - set(self.served)
        )
        return {
            "differing": [
                f"{window}: served {self.served[window]}, "
                f"shadow {self.shadowed[window]}; a logic "
                "change to explain"
                for window in differing
            ],
            "old_only": [
                f"{window}: the shadow's watermark is likely "
                "behind"
                for window in old_only
            ],
            "new_only": [
                f"{window}: the shadow is likely firing early"
                for window in new_only
            ],
        }

    def explain(self, window: str) -> None:
        self.explained.add(window)

    def promotion_gate(self) -> str:
        compared = [
            window
            for window in self.served
            if window in self.shadowed
        ]
        if len(compared) < PROMOTION_QUOTA:
            return (
                f"HOLD: {len(compared)} of {PROMOTION_QUOTA} "
                "windows compared; the shadow has not earned "
                "an opinion yet"
            )
        agreeing = sum(
            1
            for window in compared
            if self.served[window] == self.shadowed[window]
        )
        share = agreeing / len(compared)
        unexplained = [
            window
            for window in compared
            if self.served[window] != self.shadowed[window]
            and window not in self.explained
        ]
        if unexplained:
            return (
                f"HOLD: {len(unexplained)} disagreement(s) "
                "unexplained; the cutover memo does not accept "
                "mysteries"
            )
        if share < AGREEMENT_BAR:
            return (
                f"HOLD: agreement {share:.0%} under the "
                f"{AGREEMENT_BAR:.0%} bar even with "
                "explanations on file"
            )
        return (
            f"PROMOTE: {agreeing} of {len(compared)} windows "
            f"agree ({share:.0%}), every disagreement "
            "explained; this memo beats the one written after "
            "serving wrong numbers for a week"
        )
