from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.fencing import FencingCoordinator


class TestRegistration:
    def test_the_first_producer_gets_epoch_zero(self):
        coord = FencingCoordinator()
        assert coord.register("orders") == 0

    def test_a_takeover_bumps_the_epoch(self):
        coord = FencingCoordinator()
        coord.register("orders")
        assert coord.register("orders") == 1
        assert coord.current_epoch("orders") == 1


class TestFencing:
    def test_the_live_producer_writes(self):
        coord = FencingCoordinator()
        epoch = coord.register("orders")
        assert coord.write("orders", epoch, "row") == "orders@0: row"

    def test_the_zombie_is_fenced_after_a_takeover(self):
        coord = FencingCoordinator()
        zombie_epoch = coord.register("orders")
        coord.register("orders")
        with pytest.raises(Halted) as caught:
            coord.write("orders", zombie_epoch, "duplicate")
        assert "has taken over" in str(caught.value)

    def test_the_new_producer_writes_after_the_takeover(self):
        coord = FencingCoordinator()
        coord.register("orders")
        live = coord.register("orders")
        assert coord.write("orders", live, "row") == "orders@1: row"


class TestRefusals:
    def test_a_write_for_an_unregistered_id_is_refused(self):
        coord = FencingCoordinator()
        with pytest.raises(Invalid):
            coord.write("ghost", 0, "row")

    def test_an_epoch_ahead_of_the_coordinator_is_refused(self):
        coord = FencingCoordinator()
        coord.register("orders")
        with pytest.raises(Invalid):
            coord.write("orders", 5, "row")
