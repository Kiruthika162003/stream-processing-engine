from __future__ import annotations

import random

import pytest

from rill.dgim import Dgim
from rill.errors import Invalid


class TestEstimate:
    def test_all_ones_estimates_within_the_half_bound(self):
        dgim = Dgim(window=16)
        for _ in range(32):
            dgim.observe(1)
        # true is 16; DGIM undercounts by at most half the oldest
        # bucket, landing on 12 here, a quarter low and inside the bound.
        assert dgim.estimate() == 12
        assert abs(dgim.estimate() - 16) <= 0.5 * 16

    def test_a_sparse_window_estimates_close(self):
        dgim = Dgim(window=100)
        for tick in range(100):
            dgim.observe(1 if tick % 20 == 0 else 0)
        assert dgim.estimate() == 4  # true is 5

    def test_an_empty_stream_estimates_zero(self):
        assert Dgim(window=10).estimate() == 0


class TestBounds:
    def test_the_relative_error_stays_under_half(self):
        rng = random.Random(7)
        window = 64
        dgim = Dgim(window=window)
        recent: list[int] = []
        worst = 0.0
        for _ in range(2000):
            bit = 1 if rng.random() < 0.4 else 0
            dgim.observe(bit)
            recent.append(bit)
            recent = recent[-window:]
            true = sum(recent)
            if true:
                worst = max(worst, abs(dgim.estimate() - true) / true)
        assert worst < 0.5

    def test_the_bucket_count_stays_logarithmic(self):
        dgim = Dgim(window=1024)
        for _ in range(4096):
            dgim.observe(1)
        assert dgim.bucket_count() < 20
        assert abs(dgim.estimate() - 1024) <= 0.5 * 1024


class TestRefusals:
    def test_a_nonpositive_window_is_refused(self):
        with pytest.raises(Invalid):
            Dgim(window=0)

    def test_a_non_bit_is_refused(self):
        with pytest.raises(Invalid):
            Dgim(window=10).observe(2)
