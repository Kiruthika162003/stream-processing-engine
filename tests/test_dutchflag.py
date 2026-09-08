from __future__ import annotations

import random

import pytest

from rill.dutchflag import three_way_partition
from rill.errors import Invalid


class TestPartition:
    def test_the_three_bands_are_ordered(self):
        arr, low, high = three_way_partition([3, 1, 2, 3, 1, 3, 2], 3)
        assert all(x < 3 for x in arr[:low])
        assert all(x == 3 for x in arr[low:high])
        assert all(x > 3 for x in arr[high:])

    def test_it_preserves_the_multiset(self):
        original = [3, 1, 2, 3, 1, 3, 2]
        arr, _, _ = three_way_partition(original, 3)
        assert sorted(arr) == sorted(original)

    def test_it_is_valid_over_random_inputs(self):
        rng = random.Random(3)
        for _ in range(500):
            values = [rng.randint(0, 5) for _ in range(rng.randint(0, 15))]
            pivot = rng.randint(0, 5)
            arr, low, high = three_way_partition(values, pivot)
            assert all(x < pivot for x in arr[:low])
            assert all(x == pivot for x in arr[low:high])
            assert all(x > pivot for x in arr[high:])
            assert sorted(arr) == sorted(values)


class TestEdges:
    def test_all_equal_go_to_the_middle_band(self):
        arr, low, high = three_way_partition([5, 5, 5], 5)
        assert (low, high) == (0, 3)
        assert arr == [5, 5, 5]

    def test_the_input_is_not_mutated(self):
        original = [3, 1, 2]
        three_way_partition(original, 2)
        assert original == [3, 1, 2]


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            three_way_partition(None, 0)
