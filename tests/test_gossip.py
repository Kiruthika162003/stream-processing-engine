from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.gossip import coverage_after, rounds_to_cover


def _peer(seed: int):
    rng = random.Random(seed)
    return rng.randrange


class TestLogarithmicSpread:
    def test_a_thousand_nodes_are_covered_in_far_fewer_than_a_thousand_rounds(self):
        rounds = rounds_to_cover(1000, fanout=3, peer=_peer(3))
        assert rounds < 30

    def test_higher_fanout_covers_in_fewer_rounds(self):
        slow = rounds_to_cover(1000, fanout=1, peer=_peer(3))
        fast = rounds_to_cover(1000, fanout=5, peer=_peer(3))
        assert slow > fast
        assert fast < 12


class TestExponentialGrowth:
    def test_coverage_multiplies_each_round(self):
        # three rounds at fanout three reaches far more than the
        # linear three times three a non-epidemic spread would give.
        covered = coverage_after(1000, fanout=3, peer=_peer(3), rounds=3)
        assert covered >= 32

    def test_a_single_node_cluster_is_already_covered(self):
        assert rounds_to_cover(1, fanout=3, peer=_peer(3)) == 0


class TestRefusals:
    def test_a_zero_size_cluster_is_refused(self):
        with pytest.raises(Invalid):
            rounds_to_cover(0, fanout=3, peer=_peer(3))

    def test_a_zero_fanout_is_refused(self):
        with pytest.raises(Invalid):
            rounds_to_cover(10, fanout=0, peer=_peer(3))
