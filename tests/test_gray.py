from __future__ import annotations

from itertools import pairwise

import pytest

from rill.errors import Invalid
from rill.gray import decode, encode, sequence


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


class TestEncodeDecode:
    def test_known_encodings(self):
        assert encode(0) == 0
        assert encode(1) == 1
        assert encode(2) == 3
        assert encode(3) == 2
        assert encode(4) == 6

    def test_decode_inverts_encode(self):
        for i in range(10000):
            assert decode(encode(i)) == i

    def test_the_three_bit_sequence(self):
        assert sequence(3) == [0, 1, 3, 2, 6, 7, 5, 4]


class TestSingleBitProperty:
    def test_adjacent_entries_and_the_wrap_differ_by_one_bit(self):
        for bits in range(1, 13):
            seq = sequence(bits)
            assert len(set(seq)) == (1 << bits)
            for a, b in pairwise(seq):
                assert _hamming(a, b) == 1
            assert _hamming(seq[-1], seq[0]) == 1


class TestRefusals:
    def test_a_negative_value_is_refused(self):
        with pytest.raises(Invalid):
            encode(-1)

    def test_a_negative_gray_is_refused(self):
        with pytest.raises(Invalid):
            decode(-1)

    def test_a_negative_bit_count_is_refused(self):
        with pytest.raises(Invalid):
            sequence(-1)
