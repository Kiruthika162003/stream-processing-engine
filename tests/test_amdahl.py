from __future__ import annotations

import pytest

from rill.amdahl import amdahl_ceiling, amdahl_speedup, gustafson_speedup
from rill.errors import Invalid

PARALLEL = 0.9  # 10 percent serial


class TestAmdahlCeiling:
    def test_the_ceiling_is_one_over_the_serial_fraction(self):
        assert round(amdahl_ceiling(PARALLEL), 1) == 10.0

    def test_speedup_approaches_but_never_passes_the_ceiling(self):
        assert amdahl_speedup(PARALLEL, 1000) < amdahl_ceiling(PARALLEL)
        assert round(amdahl_speedup(PARALLEL, 1000), 1) == 9.9


class TestGustafsonScales:
    def test_scaled_speedup_is_near_linear(self):
        assert round(gustafson_speedup(PARALLEL, 1000), 1) == 900.1

    def test_gustafson_beats_amdahl_at_every_core_count(self):
        for cores in (10, 100, 1000):
            assert gustafson_speedup(PARALLEL, cores) > amdahl_speedup(
                PARALLEL, cores
            )


class TestRefusals:
    def test_a_fraction_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            amdahl_speedup(1.5, 10)

    def test_the_ceiling_at_full_parallelism_is_refused(self):
        with pytest.raises(Invalid):
            amdahl_ceiling(1.0)

    def test_zero_cores_is_refused(self):
        with pytest.raises(Invalid):
            gustafson_speedup(0.5, 0)
