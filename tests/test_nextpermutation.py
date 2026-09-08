from __future__ import annotations

import math

import pytest

from rill.errors import Invalid
from rill.nextpermutation import next_permutation


class TestStep:
    def test_a_single_step(self):
        items = [1, 2, 3]
        assert next_permutation(items) is True
        assert items == [1, 3, 2]

    def test_the_last_permutation_wraps_to_the_first(self):
        items = [3, 2, 1]
        assert next_permutation(items) is False
        assert items == [1, 2, 3]

    def test_a_suffix_only_change(self):
        items = [1, 3, 2]
        next_permutation(items)
        assert items == [2, 1, 3]


class TestFullCycle:
    def test_it_visits_every_permutation_once_in_order(self):
        for n in range(7):
            cur = list(range(n))
            seen = [tuple(cur)]
            while next_permutation(cur):
                seen.append(tuple(cur))
            assert len(set(seen)) == math.factorial(n)
            assert seen == sorted(seen)

    def test_duplicates_visit_only_distinct_multiset_permutations(self):
        cur = [1, 1, 2]
        seen = [tuple(cur)]
        while next_permutation(cur):
            seen.append(tuple(cur))
        assert seen == [(1, 1, 2), (1, 2, 1), (2, 1, 1)]


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            next_permutation(None)
