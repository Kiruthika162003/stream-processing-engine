from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.mos import count_distinct_queries


class TestDistinct:
    def test_a_concrete_set_of_queries(self):
        got = count_distinct_queries([1, 1, 2, 1, 3], [(0, 4), (0, 1), (2, 4), (1, 3)])
        assert got == [3, 1, 3, 2]

    def test_a_single_element_range(self):
        assert count_distinct_queries([5, 5, 5], [(1, 1)]) == [1]

    def test_it_matches_brute_recomputation(self):
        rng = random.Random(19)
        for _ in range(2000):
            n = rng.randint(1, 40)
            values = [rng.randint(0, 6) for _ in range(n)]
            queries = []
            for _ in range(rng.randint(1, 15)):
                a, b = rng.randint(0, n - 1), rng.randint(0, n - 1)
                queries.append((min(a, b), max(a, b)))
            got = count_distinct_queries(values, queries)
            brute = [len(set(values[lo : hi + 1])) for lo, hi in queries]
            assert got == brute

    def test_the_original_query_order_is_preserved(self):
        # answers come back aligned to the input order, not Mo's sorted order
        values = [1, 2, 3, 4, 5]
        got = count_distinct_queries(values, [(4, 4), (0, 4), (0, 0)])
        assert got == [1, 5, 1]


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            count_distinct_queries(None, [])

    def test_an_out_of_range_query_is_refused(self):
        with pytest.raises(Invalid):
            count_distinct_queries([1, 2, 3], [(0, 5)])

    def test_a_reversed_range_is_refused(self):
        with pytest.raises(Invalid):
            count_distinct_queries([1, 2, 3], [(2, 1)])
