from __future__ import annotations

import pytest

from rill.adaptivesample import AdaptiveSampler
from rill.errors import Invalid


class TestSteadyOutput:
    def test_below_the_target_it_samples_everything(self):
        sampler = AdaptiveSampler(target_rate=100)
        assert sampler.probability(50) == 1.0
        assert sampler.expected_output(50) == 50.0

    def test_above_the_target_the_output_stays_at_the_target(self):
        sampler = AdaptiveSampler(target_rate=100)
        assert sampler.expected_output(1000) == 100.0
        assert sampler.expected_output(10000) == 100.0

    def test_a_burst_lowers_the_probability_in_proportion(self):
        sampler = AdaptiveSampler(target_rate=100)
        assert sampler.probability(1000) == 0.1
        assert sampler.probability(10000) == 0.01


class TestContrastWithFixed:
    def test_fixed_sampling_would_flood_on_a_burst(self):
        sampler = AdaptiveSampler(target_rate=100)
        # adaptive holds 100 where a fixed 10% would emit 1000
        assert sampler.expected_output(10000) == 100.0
        assert 0.1 * 10000 == 1000.0


class TestRefusals:
    def test_a_nonpositive_target_is_refused(self):
        with pytest.raises(Invalid):
            AdaptiveSampler(target_rate=0)

    def test_a_negative_observed_rate_is_refused(self):
        with pytest.raises(Invalid):
            AdaptiveSampler(target_rate=100).probability(-1)
