from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.pipelinethroughput import (
    bottleneck_stage,
    throughput,
    throughput_after,
)

RATES = [100, 40, 80, 60]  # stage 1 is the bottleneck at 40


class TestThroughput:
    def test_the_slowest_stage_sets_the_rate(self):
        assert throughput(RATES) == 40

    def test_the_bottleneck_is_the_slowest_stage(self):
        assert bottleneck_stage(RATES) == 1


class TestWhereEffortHelps:
    def test_speeding_a_non_bottleneck_stage_does_nothing(self):
        # stage 2 was 80, already faster than the 40 bottleneck
        assert throughput_after(RATES, 2, 1000) == 40

    def test_speeding_the_bottleneck_lifts_to_the_next_slowest(self):
        # relieving stage 1 makes stage 3 (60) the new bottleneck
        assert throughput_after(RATES, 1, 200) == 60


class TestRefusals:
    def test_no_stages_is_refused(self):
        with pytest.raises(Invalid):
            throughput([])

    def test_a_nonpositive_rate_is_refused(self):
        with pytest.raises(Invalid):
            throughput([100, 0, 80])

    def test_a_stage_index_out_of_range_is_refused(self):
        with pytest.raises(Invalid):
            throughput_after(RATES, 9, 100)
