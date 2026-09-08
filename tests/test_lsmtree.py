from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.lsmtree import SizeTieredLSM


def _run(tier: int, flushes: int) -> SizeTieredLSM:
    lsm = SizeTieredLSM(tier=tier)
    for _ in range(flushes):
        lsm.flush(1)
    return lsm


class TestTheTradeoff:
    def test_a_small_tier_reads_cheap_and_writes_dear(self):
        lsm = _run(tier=2, flushes=1000)
        assert lsm.read_amplification() == 6
        assert round(lsm.write_amplification(), 2) == 9.12

    def test_a_large_tier_writes_cheap_and_reads_dear(self):
        lsm = _run(tier=8, flushes=1000)
        assert lsm.read_amplification() == 13
        assert round(lsm.write_amplification(), 2) == 3.47

    def test_raising_the_tier_lowers_write_and_raises_read(self):
        small = _run(tier=2, flushes=1000)
        large = _run(tier=8, flushes=1000)
        assert large.write_amplification() < small.write_amplification()
        assert large.read_amplification() > small.read_amplification()


class TestMerging:
    def test_a_clean_power_folds_into_a_single_run(self):
        lsm = _run(tier=2, flushes=1024)
        assert lsm.read_amplification() == 1


class TestRefusals:
    def test_a_tier_below_two_is_refused(self):
        with pytest.raises(Invalid):
            SizeTieredLSM(tier=1)

    def test_a_nonpositive_flush_is_refused(self):
        with pytest.raises(Invalid):
            SizeTieredLSM(tier=2).flush(0)

    def test_write_amplification_before_ingest_is_refused(self):
        with pytest.raises(Invalid):
            SizeTieredLSM(tier=2).write_amplification()
