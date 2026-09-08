from __future__ import annotations

import pytest

from rill.backfilltag import MetricHistory
from rill.errors import Invalid


def history() -> MetricHistory:
    built = MetricHistory(metric="daily-revenue")
    built.publish(20260901, 94000)
    return built


class TestPublishing:
    def test_the_original_reads_plainly(self):
        assert history().read(20260901) == "94000 (original)"

    def test_republishing_is_routed_to_restate(self):
        built = history()
        with pytest.raises(Invalid) as caught:
            built.publish(20260901, 80000)
        assert "corrections go through restate" in str(
            caught.value
        )


class TestRestatement:
    def test_the_restatement_shows_both_numbers(self):
        built = history()
        verdict = built.restate(
            20260901, 88000, "late refunds folded in"
        )
        assert "restated 94000 -> 88000" in verdict
        assert "the alert recognizes a correction" in verdict

    def test_the_read_carries_the_provenance(self):
        built = history()
        built.restate(
            20260901, 88000, "late refunds folded in"
        )
        read = built.read(20260901)
        assert read.startswith("88000 (RESTATED from 94000")
        assert "2 version(s) on record" in read

    def test_a_reasonless_restatement_is_a_silent_edit(self):
        built = history()
        with pytest.raises(Invalid) as caught:
            built.restate(20260901, 88000, "  ")
        assert "silent edit wearing a version number" in str(
            caught.value
        )


class TestTheTrail:
    def test_the_trail_is_append_only(self):
        built = history()
        built.restate(20260901, 88000, "refunds")
        built.restate(20260901, 87500, "one more late refund")
        trail = built.audit_trail(20260901)
        assert "v0: 94000 (original)" in trail
        assert "v2: 87500 (one more late refund)" in trail
        assert "nobody can trust in an audit" in trail
