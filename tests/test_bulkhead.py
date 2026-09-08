from __future__ import annotations

import pytest

from rill.bulkhead import Bulkhead, SharedPool
from rill.errors import Invalid


class TestSharedPoolCouples:
    def test_one_tenant_can_starve_the_shared_pool(self):
        pool = SharedPool(total=4)
        assert all(pool.acquire("greedy") for _ in range(4))
        assert not pool.acquire("victim")
        assert pool.available() == 0


class TestBulkheadContains:
    def test_a_tenant_is_capped_at_its_own_partition(self):
        bulk = Bulkhead(per_partition=2)
        assert bulk.acquire("greedy")
        assert bulk.acquire("greedy")
        assert not bulk.acquire("greedy")

    def test_the_flood_does_not_reach_the_other_partition(self):
        bulk = Bulkhead(per_partition=2)
        bulk.acquire("greedy")
        bulk.acquire("greedy")
        assert bulk.acquire("victim")
        assert bulk.available("victim") == 1

    def test_releasing_a_slot_returns_it_to_the_partition(self):
        bulk = Bulkhead(per_partition=2)
        bulk.acquire("t")
        bulk.acquire("t")
        bulk.release("t")
        assert bulk.acquire("t")


class TestRefusals:
    def test_a_nonpositive_partition_is_refused(self):
        with pytest.raises(Invalid):
            Bulkhead(per_partition=0)

    def test_releasing_an_empty_partition_is_refused(self):
        with pytest.raises(Invalid):
            Bulkhead(per_partition=2).release("t")

    def test_a_nonpositive_pool_is_refused(self):
        with pytest.raises(Invalid):
            SharedPool(total=0)
