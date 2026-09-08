from __future__ import annotations

import pytest

from rill.deltaencode import (
    delta_encode,
    encoded_size,
    raw_size,
    varint_size,
)
from rill.errors import Invalid


class TestDelta:
    def test_delta_encoding_keeps_the_head_and_the_gaps(self):
        assert delta_encode([1000000, 1000005, 1000009]) == [1000000, 5, 4]

    def test_an_unsorted_list_is_refused(self):
        with pytest.raises(Invalid):
            delta_encode([5, 3])


class TestVarint:
    def test_varint_sizes_scale_with_magnitude(self):
        assert varint_size(5) == 1
        assert varint_size(127) == 1
        assert varint_size(128) == 2
        assert varint_size(1000000) == 3


class TestCompression:
    def test_small_gaps_compress_by_the_width_ratio(self):
        offsets = [1000000 + 5 * i for i in range(1000)]
        assert encoded_size(offsets) == 1002
        assert raw_size(offsets) == 8000
        assert raw_size(offsets) // encoded_size(offsets) == 7  # ~8x

    def test_large_jumps_cost_more_per_delta(self):
        small_gaps = [i for i in range(100)]
        big_jumps = [i * 100000 for i in range(100)]
        assert encoded_size(big_jumps) > encoded_size(small_gaps)


class TestRefusals:
    def test_a_negative_varint_is_refused(self):
        with pytest.raises(Invalid):
            varint_size(-1)

    def test_no_offsets_is_refused(self):
        with pytest.raises(Invalid):
            encoded_size([])
