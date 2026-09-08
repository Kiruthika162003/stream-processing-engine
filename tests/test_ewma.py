from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.ewma import Ewma


class TestWarmupBias:
    def test_the_raw_average_reads_low_on_the_first_sample(self):
        ewma = Ewma(alpha=0.1)
        ewma.update(100)
        assert round(ewma.raw(), 2) == 10.0

    def test_the_corrected_average_is_right_from_the_first_sample(self):
        ewma = Ewma(alpha=0.1)
        ewma.update(100)
        assert round(ewma.corrected(), 2) == 100.0

    def test_the_raw_average_crawls_up_while_corrected_holds(self):
        ewma = Ewma(alpha=0.1)
        for _ in range(5):
            ewma.update(100)
        assert round(ewma.raw(), 2) == 40.95
        assert round(ewma.corrected(), 2) == 100.0

    def test_the_raw_average_eventually_converges(self):
        ewma = Ewma(alpha=0.1)
        for _ in range(50):
            ewma.update(100)
        assert round(ewma.raw(), 2) == 99.48


class TestAlphaOne:
    def test_alpha_one_tracks_the_sample_with_no_smoothing(self):
        ewma = Ewma(alpha=1.0)
        ewma.update(42)
        assert ewma.raw() == 42


class TestRefusals:
    def test_an_alpha_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            Ewma(alpha=0.0)

    def test_corrected_before_any_sample_is_refused(self):
        with pytest.raises(Invalid):
            Ewma(alpha=0.5).corrected()
