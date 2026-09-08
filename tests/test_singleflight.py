from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.singleflight import FETCH, WAIT, SingleFlight


class TestCollapse:
    def test_the_first_caller_fetches_and_the_rest_wait(self):
        flight = SingleFlight()
        verdicts = [flight.request("hot") for _ in range(100)]
        assert verdicts[0] == FETCH
        assert set(verdicts[1:]) == {WAIT}
        assert flight.upstream_fetches() == 1

    def test_resolve_serves_every_waiter_from_the_one_fetch(self):
        flight = SingleFlight()
        for _ in range(100):
            flight.request("hot")
        assert flight.resolve("hot", "value") == 100
        assert flight.in_flight() == []


class TestScope:
    def test_different_keys_fetch_independently(self):
        flight = SingleFlight()
        assert flight.request("a") == FETCH
        assert flight.request("b") == FETCH
        assert flight.upstream_fetches() == 2

    def test_a_new_miss_after_resolve_starts_a_fresh_fetch(self):
        flight = SingleFlight()
        flight.request("hot")
        flight.resolve("hot", "v1")
        assert flight.request("hot") == FETCH
        assert flight.upstream_fetches() == 2


class TestRefusals:
    def test_resolving_a_key_with_no_fetch_is_refused(self):
        flight = SingleFlight()
        with pytest.raises(Invalid):
            flight.resolve("ghost", "v")
