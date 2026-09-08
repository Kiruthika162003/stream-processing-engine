from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.floyd import cycle_length, cycle_start, has_cycle


def _chain(mapping: dict[str, str]):
    return mapping.get


class TestDetection:
    def test_a_looping_chain_has_a_cycle(self):
        succ = _chain({"A": "B", "B": "C", "C": "D", "D": "B"})
        assert has_cycle(succ, "A")

    def test_a_straight_chain_has_no_cycle(self):
        succ = _chain({"A": "B", "B": "C"})
        assert not has_cycle(succ, "A")

    def test_a_self_loop_is_a_cycle(self):
        succ = _chain({"A": "A"})
        assert has_cycle(succ, "A")


class TestCycleShape:
    def test_it_finds_where_the_loop_begins(self):
        succ = _chain({"A": "B", "B": "C", "C": "D", "D": "B"})
        assert cycle_start(succ, "A") == "B"

    def test_it_measures_the_loop_length(self):
        succ = _chain({"A": "B", "B": "C", "C": "D", "D": "B"})
        assert cycle_length(succ, "A") == 3  # B, C, D

    def test_a_self_loop_has_length_one(self):
        succ = _chain({"A": "A"})
        assert cycle_length(succ, "A") == 1


class TestRefusals:
    def test_finding_the_start_of_no_cycle_is_refused(self):
        succ = _chain({"A": "B"})
        with pytest.raises(Invalid):
            cycle_start(succ, "A")
