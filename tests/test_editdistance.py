from __future__ import annotations

import pytest

from rill.editdistance import edit_distance
from rill.errors import Invalid


class TestDistance:
    def test_the_classic_kitten_to_sitting(self):
        assert edit_distance("kitten", "sitting") == 3

    def test_identical_strings_are_zero_apart(self):
        assert edit_distance("abc", "abc") == 0

    def test_the_empty_string_costs_the_other_length(self):
        assert edit_distance("", "abc") == 3
        assert edit_distance("abc", "") == 3


class TestSubstitutionIsOneEdit:
    def test_a_single_substitution_costs_one_not_two(self):
        assert edit_distance("cat", "bat") == 1


class TestMetric:
    def test_it_is_symmetric(self):
        assert edit_distance("flaw", "lawn") == edit_distance("lawn", "flaw")


class TestRefusals:
    def test_a_none_string_is_refused(self):
        with pytest.raises(Invalid):
            edit_distance(None, "abc")
