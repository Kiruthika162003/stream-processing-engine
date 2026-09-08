from __future__ import annotations

import random

import pytest

from rill.coordcompress import Compressor
from rill.errors import Invalid


class TestCompress:
    def test_a_concrete_compression(self):
        c = Compressor([100, 5, 100, 900, 5])
        assert len(c) == 3
        assert c.compress([5, 100, 900, 5]) == [0, 1, 2, 0]

    def test_ranks_are_dense_and_start_at_zero(self):
        c = Compressor([50, 50, 900, -3])
        assert sorted(set(c.compress([50, 900, -3]))) == [0, 1, 2]

    def test_it_is_order_preserving_and_round_trips(self):
        rng = random.Random(47)
        for _ in range(3000):
            values = [rng.randint(-(10**9), 10**9) for _ in range(rng.randint(1, 30))]
            c = Compressor(values)
            comp = c.compress(values)
            for i in range(len(values)):
                for j in range(len(values)):
                    assert (values[i] < values[j]) == (comp[i] < comp[j])
            assert all(c.value(r) == v for v, r in zip(values, comp, strict=True))
            assert set(comp) == set(range(len(set(values))))


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            Compressor(None)

    def test_an_absent_value_is_refused(self):
        c = Compressor([1, 2, 3])
        with pytest.raises(Invalid):
            c.rank(99)

    def test_an_out_of_range_rank_is_refused(self):
        c = Compressor([1, 2, 3])
        with pytest.raises(Invalid):
            c.value(5)
