from __future__ import annotations

import pytest

from rill.creditflow import CreditChannel, CreditMultiplexer
from rill.errors import Halted, Invalid


class TestSingleChannel:
    def test_a_channel_starts_with_a_full_credit(self):
        channel = CreditChannel(capacity=3)
        assert channel.credit() == 3

    def test_sending_spends_credit_down_to_the_buffer(self):
        channel = CreditChannel(capacity=2)
        channel.send()
        channel.send()
        assert not channel.can_send()

    def test_overrunning_the_buffer_is_halted(self):
        channel = CreditChannel(capacity=1)
        channel.send()
        with pytest.raises(Halted) as caught:
            channel.send()
        assert "receiver's buffer is full" in str(caught.value)

    def test_draining_grants_the_credit_back(self):
        channel = CreditChannel(capacity=2)
        channel.send()
        channel.send()
        channel.drain(1)
        assert channel.credit() == 1
        channel.send()
        assert channel.credit() == 0


class TestIsolation:
    def test_a_stalled_channel_does_not_starve_its_sibling(self):
        mux = CreditMultiplexer(capacity=2)
        mux.send("slow")
        mux.send("slow")
        assert not mux.channel("slow").can_send()
        assert "fast" in mux.sendable()
        mux.send("fast")
        assert mux.channel("fast").credit() == 1

    def test_the_stalled_channel_is_the_only_one_missing(self):
        mux = CreditMultiplexer(capacity=1)
        mux.send("a")
        mux.send("b")
        mux.channel("c")
        assert mux.sendable() == ["c"]


class TestRefusals:
    def test_a_nonpositive_capacity_is_refused(self):
        with pytest.raises(Invalid):
            CreditChannel(capacity=0)

    def test_draining_more_than_is_in_flight_is_refused(self):
        channel = CreditChannel(capacity=3)
        channel.send()
        with pytest.raises(Invalid):
            channel.drain(2)
