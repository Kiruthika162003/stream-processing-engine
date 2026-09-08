from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.gcra import Gcra


class TestBurst:
    def test_a_quiet_source_may_burst_up_to_the_tolerance(self):
        # tolerance 30 over interval 10 allows about four at once
        gcra = Gcra(interval=10, tolerance=30)
        burst = sum(1 for _ in range(10) if gcra.allow(0))
        assert burst == 4

    def test_after_the_burst_it_settles_to_the_rate(self):
        gcra = Gcra(interval=10, tolerance=30)
        for _ in range(4):
            gcra.allow(0)
        assert not gcra.allow(0)  # burst spent
        assert gcra.allow(40)  # one interval past the burst window


class TestSteadyRate:
    def test_it_admits_one_per_interval_with_no_tolerance(self):
        gcra = Gcra(interval=10, tolerance=0)
        assert [t for t in range(0, 50, 10) if gcra.allow(t)] == [0, 10, 20, 30, 40]

    def test_an_early_retry_is_rejected(self):
        gcra = Gcra(interval=10, tolerance=0)
        gcra.allow(0)
        assert not gcra.allow(1)
        assert gcra.allow(10)


class TestRefusals:
    def test_a_nonpositive_interval_is_refused(self):
        with pytest.raises(Invalid):
            Gcra(interval=0, tolerance=10)

    def test_a_negative_tolerance_is_refused(self):
        with pytest.raises(Invalid):
            Gcra(interval=10, tolerance=-1)
