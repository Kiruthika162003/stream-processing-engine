from __future__ import annotations

import itertools
import random

import pytest

from rill.errors import Invalid
from rill.jobsequencing import max_profit


def _brute(jobs: list[tuple[int, int]]) -> int:
    best = 0
    for size in range(len(jobs) + 1):
        for order in itertools.permutations(jobs, size):
            if all(slot <= deadline for slot, (deadline, _) in enumerate(order, 1)):
                best = max(best, sum(profit for _, profit in order))
    return best


class TestGreedy:
    def test_the_classic_instance(self):
        jobs = [(2, 100), (1, 19), (2, 27), (1, 25), (3, 15)]
        assert max_profit(jobs) == (142, 3)

    def test_it_matches_brute_force(self):
        rng = random.Random(2)
        for _ in range(200):
            jobs = [
                (rng.randint(1, 5), rng.randint(1, 20))
                for _ in range(rng.randint(0, 6))
            ]
            assert max_profit(jobs)[0] == _brute(jobs)


class TestEdges:
    def test_no_jobs_earns_nothing(self):
        assert max_profit([]) == (0, 0)

    def test_jobs_sharing_deadline_one_keep_only_the_richest(self):
        jobs = [(1, 10), (1, 50), (1, 30)]
        assert max_profit(jobs) == (50, 1)


class TestRefusals:
    def test_a_deadline_below_one_is_refused(self):
        with pytest.raises(Invalid):
            max_profit([(0, 5)])

    def test_a_negative_profit_is_refused(self):
        with pytest.raises(Invalid):
            max_profit([(1, -5)])
