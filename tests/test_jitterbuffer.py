from __future__ import annotations

import random

import pytest

from rill.errors import Invalid
from rill.jitterbuffer import playout

INTERVAL = 20


def _arrivals() -> list[tuple[int, int]]:
    rng = random.Random(5)
    return [(seq, seq * INTERVAL + rng.randint(0, 80)) for seq in range(200)]


class TestTheTrade:
    def test_zero_delay_drops_nearly_everything(self):
        _, dropped = playout(_arrivals(), INTERVAL, 0)
        assert dropped == 197

    def test_a_middling_delay_drops_the_jitter_beyond_it(self):
        _, dropped = playout(_arrivals(), INTERVAL, 40)
        assert dropped == 94

    def test_a_delay_covering_the_jitter_drops_nothing(self):
        played, dropped = playout(_arrivals(), INTERVAL, 80)
        assert dropped == 0
        assert played == 200

    def test_more_delay_never_drops_more(self):
        arrivals = _arrivals()
        small = playout(arrivals, INTERVAL, 20)[1]
        large = playout(arrivals, INTERVAL, 60)[1]
        assert large <= small


class TestRefusals:
    def test_no_packets_is_refused(self):
        with pytest.raises(Invalid):
            playout([], INTERVAL, 40)

    def test_a_negative_delay_is_refused(self):
        with pytest.raises(Invalid):
            playout([(0, 0)], INTERVAL, -1)
