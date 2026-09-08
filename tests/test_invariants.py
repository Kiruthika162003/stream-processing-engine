from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.invariants import InvariantMonitor


def balance_monitor() -> InvariantMonitor:
    return InvariantMonitor(
        name="balance-never-negative",
        version=1,
        check=lambda value, state: state + value >= 0,
    )


class TestTheMonitor:
    def test_consistent_events_pass_quietly(self):
        monitor = balance_monitor()
        assert monitor.observe("evt-1", -30, state=100) == (
            "evt-1 consistent"
        )

    def test_the_impossible_is_quarantined_with_context(self):
        monitor = balance_monitor()
        verdict = monitor.observe("evt-2", -500, state=100)
        assert verdict.startswith("QUARANTINED evt-2")
        assert "value -500 against state 100" in verdict
        assert "denial of service" in verdict
        assert len(monitor.quarantined) == 1

    def test_versionless_invariants_are_refused(self):
        with pytest.raises(Invalid):
            InvariantMonitor(
                name="x", version=0, check=lambda _v, _s: True
            )


class TestEscalation:
    def test_one_violation_is_a_bug_report(self):
        monitor = balance_monitor()
        monitor.observe("evt-1", -500, state=0)
        assert "a bug report" in monitor.escalation()

    def test_a_burst_is_a_corrupted_upstream_or_worse(self):
        monitor = balance_monitor()
        for number in range(4):
            monitor.observe(f"evt-{number}", -500, state=0)
        verdict = monitor.escalation()
        assert "corrupted upstream or a wrong invariant" in (
            verdict
        )

    def test_the_window_closes_and_resets(self):
        monitor = balance_monitor()
        monitor.observe("evt-1", -500, state=0)
        monitor.close_window()
        assert monitor.escalation() == (
            "balance-never-negative: quiet window"
        )


class TestRevision:
    def test_the_wrong_invariant_is_revised_not_stormed(self):
        monitor = balance_monitor()
        verdict = monitor.revise(
            lambda value, state: state + value >= -1000
        )
        assert "revised to v2" in verdict
        assert "it was a wrong invariant" in verdict
        assert monitor.observe("evt-9", -500, state=0) == (
            "evt-9 consistent"
        )
