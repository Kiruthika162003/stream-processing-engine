from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.spillover import SpillStore


def small_store() -> SpillStore:
    store = SpillStore(memory_capacity=2)
    store.put("a", 1)
    store.put("b", 2)
    store.put("c", 3)
    return store


class TestTheTiers:
    def test_the_coldest_key_spills_first(self):
        store = small_store()
        assert "a" in store.cold
        assert set(store.hot) == {"b", "c"}

    def test_the_cold_read_pays_disk_and_promotes(self):
        store = small_store()
        value, story = store.get("a")
        assert value == 1
        assert "disk latency paid, promoted back" in story
        assert "a" in store.hot

    def test_the_hot_read_is_memory_speed(self):
        store = small_store()
        value, story = store.get("c")
        assert (value, story) == (3, "memory speed")

    def test_never_seen_is_its_own_answer(self):
        assert small_store().get("ghost") == (
            None,
            "never seen",
        )

    def test_a_memoryless_store_is_refused(self):
        with pytest.raises(Invalid):
            SpillStore(memory_capacity=0)


class TestTheBet:
    def test_a_holding_hot_set_grades_well(self):
        store = SpillStore(memory_capacity=3)
        for key, value in (("a", 1), ("b", 2), ("c", 3)):
            store.put(key, value)
        for _ in range(10):
            store.get("a")
            store.get("b")
        verdict = store.thrash_check()
        assert verdict.startswith("0% of reads promoted")
        assert "the hot set is holding" in verdict

    def test_thrash_is_called_before_the_latency_graph(self):
        store = SpillStore(memory_capacity=2)
        for round_number in range(4):
            for key in ("a", "b", "c", "d"):
                store.put(key, round_number)
        for _ in range(3):
            for key in ("a", "b", "c", "d"):
                store.get(key)
        verdict = store.thrash_check()
        assert verdict.startswith("THRASH:")
        assert "memory's bookkeeping" in verdict

    def test_an_unread_store_cannot_be_graded(self):
        with pytest.raises(Invalid):
            small_store().thrash_check()
