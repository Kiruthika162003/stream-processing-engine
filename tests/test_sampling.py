from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.sampling import HashSampler, joinability_drill

IDS = [f"req-{number}" for number in range(2000)]


class TestTheDecision:
    def test_the_same_event_is_always_in_or_always_out(self):
        first = HashSampler(rate_permille=100)
        second = HashSampler(rate_permille=100)
        for identity in IDS[:200]:
            assert first.admit(identity) == second.admit(
                identity
            )

    def test_identityless_events_cannot_be_sampled(self):
        with pytest.raises(Invalid):
            HashSampler(rate_permille=10).admit("")

    def test_wild_rates_are_refused(self):
        with pytest.raises(Invalid):
            HashSampler(rate_permille=0)
        with pytest.raises(Invalid):
            HashSampler(rate_permille=2000)


class TestTheMeter:
    def test_the_realized_rate_is_printed_with_its_drift(self):
        sampler = HashSampler(rate_permille=100)
        for identity in IDS:
            sampler.admit(identity)
        line = sampler.realized()
        assert line.startswith("requested 100 per mille")
        assert "small streams wander" in line
        assert 160 <= sampler.kept <= 240

    def test_an_unused_sampler_has_no_rate(self):
        with pytest.raises(Invalid):
            HashSampler(rate_permille=10).realized()


class TestJoinability:
    def test_the_two_streams_share_their_sample(self):
        verdict = joinability_drill(IDS)
        assert "identical membership" in verdict
        assert "the samples join" in verdict

    def test_an_empty_drill_is_refused(self):
        with pytest.raises(Invalid):
            joinability_drill([])
