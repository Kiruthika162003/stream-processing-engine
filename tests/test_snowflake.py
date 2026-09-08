from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.snowflake import MAX_SEQ, SnowflakeGenerator


class TestOrdering:
    def test_ids_sort_by_creation_time(self):
        gen = SnowflakeGenerator(node_id=5, epoch=1000)
        first = gen.next_id(2000)
        second = gen.next_id(2000)
        third = gen.next_id(2001)
        assert first < second < third

    def test_two_nodes_do_not_collide_in_the_same_millisecond(self):
        left = SnowflakeGenerator(node_id=1)
        right = SnowflakeGenerator(node_id=2)
        assert left.next_id(100) != right.next_id(100)


class TestClockBetrayals:
    def test_the_sequence_exhausts_within_one_millisecond(self):
        gen = SnowflakeGenerator(node_id=1)
        for _ in range(MAX_SEQ + 1):
            gen.next_id(100)
        with pytest.raises(Halted):
            gen.next_id(100)

    def test_the_sequence_resets_on_the_next_millisecond(self):
        gen = SnowflakeGenerator(node_id=1)
        for _ in range(MAX_SEQ + 1):
            gen.next_id(100)
        # the next millisecond frees the sequence again
        assert gen.next_id(101) is not None

    def test_a_backward_clock_is_refused(self):
        gen = SnowflakeGenerator(node_id=1)
        gen.next_id(100)
        with pytest.raises(Invalid) as caught:
            gen.next_id(99)
        assert "clock went backward" in str(caught.value)


class TestRefusals:
    def test_an_out_of_range_node_id_is_refused(self):
        with pytest.raises(Invalid):
            SnowflakeGenerator(node_id=99999)
