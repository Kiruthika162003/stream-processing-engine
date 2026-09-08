from __future__ import annotations

import pytest

from rill.content_hash import stable_bucket, stable_digest
from rill.errors import Invalid
from rill.partitions import Partitioner


class TestTheHash:
    def test_the_digest_is_stable_across_calls(self):
        assert stable_digest("user-7") == stable_digest("user-7")
        assert len(stable_digest("user-7")) == 32

    def test_buckets_stay_in_range(self):
        for number in range(50):
            assert 0 <= stable_bucket(f"k{number}", 4) < 4

    def test_zero_buckets_is_refused(self):
        with pytest.raises(Invalid):
            stable_bucket("x", 0)


class TestRouting:
    def test_a_key_never_moves_between_restarts(self):
        first = Partitioner(partitions=4)
        second = Partitioner(partitions=4)
        for key in ("alice", "bob", "carol"):
            assert first.route(key) == second.route(key)

    def test_a_keyless_event_routes_nowhere(self):
        with pytest.raises(Invalid):
            Partitioner(partitions=2).route("")


class TestSkew:
    def test_spread_keys_keep_the_promise(self):
        router = Partitioner(partitions=4)
        for number in range(200):
            router.route(f"key{number}")
        verdict = router.skew_verdict()
        assert "the promise of parallelism holds" in verdict

    def test_the_famous_key_is_named_with_its_share(self):
        router = Partitioner(partitions=4)
        for _ in range(90):
            router.route("bieber")
        for number in range(10):
            router.route(f"quiet{number}")
        verdict = router.skew_verdict()
        assert verdict.startswith("SKEWED")
        assert "bieber (90%)" in verdict
        assert "key-level decisions" in verdict

    def test_balance_before_any_events_is_a_rumor(self):
        with pytest.raises(Invalid):
            Partitioner(partitions=2).balance()
