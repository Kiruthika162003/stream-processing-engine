from __future__ import annotations

import pytest

from rill.boundedstaleness import BoundedStaleness
from rill.errors import Invalid, Missing


class TestStalenessBound:
    def test_a_fresh_enough_replica_is_served(self):
        store = BoundedStaleness(max_lag=2)
        for _ in range(5):
            store.leader_write()  # leader at version 5
        assert store.read(3) == 3  # two behind, within the bound

    def test_a_too_stale_replica_is_refused(self):
        store = BoundedStaleness(max_lag=2)
        for _ in range(5):
            store.leader_write()
        with pytest.raises(Missing) as caught:
            store.read(2)  # three behind, past the bound
        assert "past the staleness bound" in str(caught.value)

    def test_the_leader_itself_is_always_fresh(self):
        store = BoundedStaleness(max_lag=0)
        store.leader_write()
        assert store.read(store.leader_version()) == 1


class TestTheTrade:
    def test_a_tighter_bound_refuses_where_a_looser_one_serves(self):
        tight = BoundedStaleness(max_lag=1)
        loose = BoundedStaleness(max_lag=5)
        for _ in range(5):
            tight.leader_write()
            loose.leader_write()
        with pytest.raises(Missing):
            tight.read(2)
        assert loose.read(2) == 2


class TestRefusals:
    def test_a_negative_bound_is_refused(self):
        with pytest.raises(Invalid):
            BoundedStaleness(max_lag=-1)

    def test_a_version_beyond_the_leader_is_refused(self):
        store = BoundedStaleness(max_lag=2)
        store.leader_write()
        with pytest.raises(Invalid):
            store.read(9)
