from __future__ import annotations

from rill.shadowpipe import ShadowRun


def agreeing_run(windows: int = 25) -> ShadowRun:
    run = ShadowRun()
    for number in range(windows):
        run.emit_old(f"[{number * 10})", 100 + number)
        run.emit_new(f"[{number * 10})", 100 + number)
    return run


class TestTriage:
    def test_the_three_species_point_at_different_parts(self):
        run = ShadowRun()
        run.emit_old("[0)", 10)
        run.emit_new("[0)", 12)
        run.emit_old("[10)", 5)
        run.emit_new("[20)", 7)
        triage = run.triage()
        assert triage["differing"] == [
            "[0): served 10, shadow 12; a logic change to "
            "explain"
        ]
        assert triage["old_only"] == [
            "[10): the shadow's watermark is likely behind"
        ]
        assert triage["new_only"] == [
            "[20): the shadow is likely firing early"
        ]


class TestTheGate:
    def test_the_shadow_must_earn_an_opinion(self):
        run = agreeing_run(windows=5)
        assert run.promotion_gate().startswith(
            "HOLD: 5 of 20 windows compared"
        )

    def test_full_agreement_promotes_with_the_memo(self):
        verdict = agreeing_run().promotion_gate()
        assert verdict.startswith(
            "PROMOTE: 25 of 25 windows agree (100%)"
        )
        assert "wrong numbers for a week" in verdict

    def test_mysteries_hold_the_gate(self):
        run = agreeing_run()
        run.emit_new("[0)", 999)
        verdict = run.promotion_gate()
        assert "does not accept mysteries" in verdict

    def test_an_explained_disagreement_can_still_promote(self):
        run = agreeing_run()
        run.emit_new("[0)", 999)
        run.explain("[0)")
        verdict = run.promotion_gate()
        assert verdict.startswith("PROMOTE: 24 of 25")
