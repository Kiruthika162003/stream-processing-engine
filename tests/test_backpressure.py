from __future__ import annotations

import pytest

from rill.backpressure import Channel, ThreeStageLine
from rill.errors import Invalid


def slowed_line() -> ThreeStageLine:
    line = ThreeStageLine()
    for now in range(3):
        line.tick(now)
    line.slow_the_sink(3)
    for now in range(4, 14):
        line.tick(now)
    return line


class TestTheChannel:
    def test_the_bound_refuses_when_full(self):
        channel = Channel("c", capacity=2)
        assert channel.offer(now=0)
        assert channel.offer(now=1)
        assert not channel.offer(now=2)
        assert channel.filled_at == 2

    def test_a_take_reopens_the_channel(self):
        channel = Channel("c", capacity=1)
        channel.offer(now=0)
        channel.offer(now=1)
        assert channel.take()
        assert channel.filled_at is None
        assert channel.offer(now=2)

    def test_a_capacityless_channel_is_refused(self):
        with pytest.raises(Invalid):
            Channel("c", capacity=0)


class TestPropagation:
    def test_the_slowness_walks_upstream_in_order(self):
        line = slowed_line()
        readout = line.incident_readout()
        assert "[3] sink slowed" in readout
        assert "[6] channel-2 filled" in readout
        assert "[8] channel-1 filled" in readout
        assert "[8] source paused" in readout
        assert readout.index("channel-2") < readout.index(
            "channel-1"
        )

    def test_the_source_pause_is_the_design_working(self):
        line = slowed_line()
        assert line.source_paused_at == 8
        assert "the design working" in line.incident_readout()

    def test_blame_points_downstream(self):
        readout = slowed_line().incident_readout()
        assert "attributed to the sink below it" in readout
        assert "attributed to stage two" in readout
        assert "the wrong team gets paged" in readout

    def test_an_empty_timeline_has_no_readout(self):
        with pytest.raises(Invalid):
            ThreeStageLine().incident_readout()
