from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.kwaymerge import merge


class TestMerge:
    def test_it_matches_a_sorted_concatenation(self):
        rng = random.Random(2)
        streams = [
            sorted(rng.randint(0, 1000) for _ in range(50)) for _ in range(20)
        ]
        expected = sorted(value for stream in streams for value in stream)
        assert merge(streams) == expected

    def test_it_interleaves_three_ordered_streams(self):
        streams = [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
        assert merge(streams) == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_empty_streams_are_skipped(self):
        assert merge([[], [1, 2], []]) == [1, 2]

    def test_a_single_stream_returns_itself(self):
        assert merge([[1, 2, 3]]) == [1, 2, 3]


class TestRefusals:
    def test_no_streams_is_refused(self):
        with pytest.raises(Invalid):
            merge([])

    def test_an_unsorted_stream_is_refused(self):
        with pytest.raises(Invalid):
            merge([[3, 1, 2]])
