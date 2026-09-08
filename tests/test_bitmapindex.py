from __future__ import annotations

import pytest

from rill.bitmapindex import BitmapIndex
from rill.errors import Invalid


class TestSingleColumn:
    def test_equality_returns_the_rows_with_that_value(self):
        index = BitmapIndex()
        colours = ["red", "blue", "red", "green"]
        for colour in colours:
            index.add(colour)
        assert index.equals("red") == {0, 2}

    def test_union_matches_any_of_the_values(self):
        index = BitmapIndex()
        for colour in ["red", "blue", "red", "green"]:
            index.add(colour)
        assert index.any_of(["blue", "green"]) == {1, 3}

    def test_complement_excludes_the_value(self):
        index = BitmapIndex()
        for colour in ["red", "blue", "red", "green"]:
            index.add(colour)
        assert index.complement("red") == {1, 3}


class TestCrossColumn:
    def test_intersection_filters_two_columns_at_once(self):
        colour = BitmapIndex()
        size = BitmapIndex()
        rows = [("red", "S"), ("red", "L"), ("blue", "L"), ("red", "L")]
        for colour_value, size_value in rows:
            colour.add(colour_value)
            size.add(size_value)
        # red AND large -> rows 1 and 3
        assert colour.both(size, "red", "L") == {1, 3}

    def test_mismatched_row_counts_are_refused(self):
        left = BitmapIndex()
        left.add("a")
        right = BitmapIndex()
        with pytest.raises(Invalid):
            left.both(right, "a", "b")


class TestBruteForceAgreement:
    def test_the_set_algebra_matches_a_scan(self):
        values = ["a", "b", "a", "c", "b", "a"]
        index = BitmapIndex()
        for value in values:
            index.add(value)
        for target in ("a", "b", "c"):
            expected = {i for i, v in enumerate(values) if v == target}
            assert index.equals(target) == expected
