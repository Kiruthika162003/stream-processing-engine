from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.luhn import check_digit, is_valid


class TestValidity:
    def test_the_check_digit_makes_a_valid_number(self):
        payload = "7992739871"
        full = payload + str(check_digit(payload))
        assert full == "79927398713"
        assert is_valid(full)


class TestErrorDetection:
    def test_a_single_digit_error_is_caught(self):
        # flip one digit of a valid number
        assert not is_valid("79927398710")

    def test_an_adjacent_transposition_is_caught(self):
        # swap the first two digits of the valid 79927398713
        assert not is_valid("97927398713")


class TestTheBlindSpot:
    def test_the_zero_nine_swap_is_missed(self):
        # 091 and 901 both validate: Luhn cannot tell 09 from 90
        assert is_valid("091")
        assert is_valid("901")


class TestRefusals:
    def test_a_non_digit_string_is_refused(self):
        with pytest.raises(Invalid):
            is_valid("12a4")

    def test_an_empty_string_is_refused(self):
        with pytest.raises(Invalid):
            check_digit("")
