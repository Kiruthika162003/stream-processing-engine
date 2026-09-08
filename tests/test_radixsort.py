from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.radixsort import radix_sort


class TestCorrectness:
    def test_the_classic_case(self):
        assert radix_sort([170, 45, 75, 90, 802, 24, 2, 66]) == [
            2, 24, 45, 66, 75, 90, 170, 802,
        ]

    def test_it_matches_the_builtin_sort(self):
        rng = random.Random(4)
        for _ in range(500):
            values = [rng.randint(0, 100000) for _ in range(rng.randint(0, 30))]
            assert radix_sort(values) == sorted(values)

    def test_it_works_in_other_bases(self):
        assert radix_sort([5, 3, 8, 1, 9, 2], base=2) == [1, 2, 3, 5, 8, 9]

    def test_empty_stays_empty(self):
        assert radix_sort([]) == []


class TestRefusals:
    def test_a_base_below_two_is_refused(self):
        with pytest.raises(Invalid):
            radix_sort([1, 2], base=1)

    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            radix_sort([-1, 2])
