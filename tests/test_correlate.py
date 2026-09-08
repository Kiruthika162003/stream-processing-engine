from __future__ import annotations

import pytest

from rill.correlate import Correlator
from rill.errors import Invalid


def correlator() -> Correlator:
    return Correlator(timeout=10)


class TestMatching:
    def test_a_request_and_response_match_with_their_latency(self):
        chosen = correlator()
        chosen.request("req-1", now=100)
        verdict = chosen.response("req-1", now=107)
        assert verdict == "req-1 matched in 7 tick(s)"
        assert chosen.matched == 1

    def test_a_response_with_no_request_is_a_bug_or_replay(self):
        chosen = correlator()
        verdict = chosen.response("ghost", now=5)
        assert "a bug or a replay, not a match" in verdict
        assert chosen.orphan_responses == ["ghost"]

    def test_a_duplicate_request_id_is_refused(self):
        chosen = correlator()
        chosen.request("req-1", now=100)
        with pytest.raises(Invalid) as caught:
            chosen.request("req-1", now=101)
        assert "makes matching ambiguous" in str(caught.value)

    def test_an_idless_request_is_refused(self):
        with pytest.raises(Invalid):
            correlator().request("", now=0)


class TestAging:
    def test_the_unanswered_request_ages_into_a_named_orphan(self):
        chosen = correlator()
        chosen.request("req-1", now=100)
        verdict = chosen.age_out(now=115)
        assert "1 request(s) orphaned past the timeout: req-1" in (
            verdict
        )
        assert "not a climbing p99" in verdict
        assert chosen.timed_out == ["req-1"]

    def test_a_fresh_request_still_has_hope(self):
        chosen = correlator()
        chosen.request("req-1", now=100)
        assert "every request still has hope" in chosen.age_out(
            now=105
        )


class TestHealth:
    def test_a_low_orphan_rate_is_the_tail(self):
        chosen = correlator()
        for number in range(9):
            chosen.request(f"r{number}", now=0)
            chosen.response(f"r{number}", now=1)
        chosen.request("late", now=0)
        chosen.age_out(now=100)
        assert "10% orphan rate: the tail" in chosen.health()

    def test_a_high_orphan_rate_names_the_downstream(self):
        chosen = correlator()
        chosen.request("ok", now=0)
        chosen.response("ok", now=1)
        for number in range(3):
            chosen.request(f"dead-{number}", now=0)
        chosen.age_out(now=100)
        assert "stopped answering, not the tail" in chosen.health()

    def test_no_completions_have_no_health(self):
        with pytest.raises(Invalid):
            correlator().health()
