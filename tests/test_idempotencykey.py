from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.idempotencykey import IdempotencyStore


class TestRunOnce:
    def test_a_retry_returns_the_cached_result_without_rerunning(self):
        store = IdempotencyStore()
        runs = {"count": 0}

        def work() -> str:
            runs["count"] += 1
            return f"result-{runs['count']}"

        first = store.execute("k1", work)
        second = store.execute("k1", work)  # a retry with the same key
        assert first == second == "result-1"
        assert runs["count"] == 1  # the work ran exactly once

    def test_different_keys_run_independently(self):
        store = IdempotencyStore()
        runs = {"count": 0}

        def work() -> str:
            runs["count"] += 1
            return str(runs["count"])

        store.execute("a", work)
        store.execute("b", work)
        assert runs["count"] == 2


class TestSeen:
    def test_a_key_is_remembered_after_execution(self):
        store = IdempotencyStore()
        assert not store.was_seen("k")
        store.execute("k", lambda: "v")
        assert store.was_seen("k")


class TestRefusals:
    def test_an_empty_key_is_refused(self):
        with pytest.raises(Invalid):
            IdempotencyStore().execute("", lambda: "v")
