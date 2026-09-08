from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.lease import FencedResource, LeaseManager


class TestLease:
    def test_a_held_lease_blocks_a_second_acquirer(self):
        manager = LeaseManager(lease_duration=10)
        manager.acquire("a", now=0)
        with pytest.raises(Halted):
            manager.acquire("b", now=5)

    def test_an_expired_lease_lets_the_next_acquirer_in(self):
        manager = LeaseManager(lease_duration=10)
        manager.acquire("a", now=0)
        assert manager.acquire("b", now=10) == 2  # a higher token

    def test_tokens_strictly_increase(self):
        manager = LeaseManager(lease_duration=10)
        first = manager.acquire("a", now=0)
        second = manager.acquire("b", now=10)
        assert second > first


class TestFencing:
    def test_the_paused_holders_stale_write_is_fenced(self):
        manager = LeaseManager(lease_duration=10)
        old_token = manager.acquire("a", now=0)
        new_token = manager.acquire("b", now=10)  # a's lease expired
        resource = FencedResource()
        resource.write(new_token, "from b")  # the live holder writes
        with pytest.raises(Halted) as caught:
            resource.write(old_token, "from paused a")
        assert "fenced" in str(caught.value)

    def test_the_current_holder_writes_freely(self):
        resource = FencedResource()
        resource.write(1, "v1")
        resource.write(2, "v2")
        assert resource.highest_token() == 2


class TestRefusals:
    def test_a_nonpositive_lease_is_refused(self):
        with pytest.raises(Invalid):
            LeaseManager(lease_duration=0)
