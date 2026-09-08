from __future__ import annotations

import random
from collections import defaultdict

import pytest

from rill.errors import Invalid
from rill.mergesort import merge_sort


class TestSorting:
    def test_it_sorts_by_key(self):
        out = merge_sort([(3, "a"), (1, "b"), (2, "c")])
        assert [k for k, _ in out] == [1, 2, 3]

    def test_a_custom_key_is_honored(self):
        # sort by the length of the tag
        out = merge_sort([(0, "ccc"), (0, "a"), (0, "bb")], key=lambda item: len(item[1]))
        assert [t for _, t in out] == ["a", "bb", "ccc"]


class TestStability:
    def test_equal_keys_keep_their_input_order(self):
        out = merge_sort([(1, "a"), (2, "b"), (1, "c"), (2, "d"), (1, "e")])
        ones = [t for k, t in out if k == 1]
        assert ones == ["a", "c", "e"]

    def test_it_is_correct_and_stable_over_random_records(self):
        rng = random.Random(3)
        for _ in range(500):
            records = [(rng.randint(0, 5), str(i)) for i in range(rng.randint(0, 20))]
            out = merge_sort(records)
            assert [k for k, _ in out] == sorted(k for k, _ in records)
            original: dict[int, list[str]] = defaultdict(list)
            for k, t in records:
                original[k].append(t)
            got: dict[int, list[str]] = defaultdict(list)
            for k, t in out:
                got[k].append(t)
            assert all(original[k] == got[k] for k in original)


class TestEdges:
    def test_empty_and_single(self):
        assert merge_sort([]) == []
        assert merge_sort([(5, "x")]) == [(5, "x")]


class TestRefusals:
    def test_none_is_refused(self):
        with pytest.raises(Invalid):
            merge_sort(None)
