from __future__ import annotations

import random
from collections import Counter

import pytest

from rill.errors import Invalid
from rill.saltedpartition import SaltedPartitioner


def _workload() -> list[str]:
    rng = random.Random(1)
    events = ["hot"] * 5000 + [f"cold-{i % 500}" for i in range(5000)]
    rng.shuffle(events)
    return events


def _max_load(partitioner: SaltedPartitioner, events: list[str]) -> int:
    rng = random.Random(2)
    loads = Counter(partitioner.route(key, lambda: rng.randint(0, 10**9)) for key in events)
    return max(loads.values())


class TestSalting:
    def test_without_salting_the_hot_key_concentrates_load(self):
        events = _workload()
        plain = SaltedPartitioner(partitions=8, salt_factor=1, hot_keys=set())
        assert _max_load(plain, events) > 5000

    def test_salting_spreads_the_hot_key_across_partitions(self):
        events = _workload()
        salted = SaltedPartitioner(partitions=8, salt_factor=8, hot_keys={"hot"})
        assert _max_load(salted, events) < 2500

    def test_salting_lowers_the_peak(self):
        events = _workload()
        plain = SaltedPartitioner(partitions=8, salt_factor=1)
        salted = SaltedPartitioner(partitions=8, salt_factor=8, hot_keys={"hot"})
        assert _max_load(salted, events) < _max_load(plain, events)


class TestColdKeys:
    def test_a_cold_key_routes_deterministically(self):
        partitioner = SaltedPartitioner(partitions=8, salt_factor=8, hot_keys={"hot"})
        first = partitioner.route("cold-1", lambda: 0)
        assert partitioner.route("cold-1", lambda: 999) == first


class TestRefusals:
    def test_a_nonpositive_partition_count_is_refused(self):
        with pytest.raises(Invalid):
            SaltedPartitioner(partitions=0, salt_factor=4)

    def test_a_nonpositive_salt_factor_is_refused(self):
        with pytest.raises(Invalid):
            SaltedPartitioner(partitions=8, salt_factor=0)
