from __future__ import annotations

import pytest

from rill.connectorhealth import ConnectorHealth
from rill.errors import Invalid


def connector() -> ConnectorHealth:
    chosen = ConnectorHealth(name="kafka-in", poll_interval=10)
    chosen.heartbeat(now=100, found_data=True)
    return chosen


class TestTheDistinction:
    def test_a_stale_heartbeat_is_a_dead_connector(self):
        chosen = connector()
        verdict = chosen.status(now=200, lag_rising=True)
        assert verdict.startswith("kafka-in DEAD")
        assert "however recent its last data looks" in verdict

    def test_rising_lag_with_a_fresh_heartbeat_is_a_slow_consumer(self):
        chosen = connector()
        chosen.heartbeat(now=105, found_data=True)
        verdict = chosen.status(now=110, lag_rising=True)
        assert "a slow consumer, not a dead source" in verdict
        assert "look downstream" in verdict

    def test_a_polling_but_empty_source_is_healthy_and_idle(self):
        chosen = connector()
        for tick in range(105, 200, 5):
            chosen.heartbeat(now=tick, found_data=False)
        verdict = chosen.status(now=200, lag_rising=False)
        assert "healthy and idle" in verdict
        assert "not a failure" in verdict

    def test_a_flowing_connector_is_plainly_healthy(self):
        chosen = connector()
        chosen.heartbeat(now=105, found_data=True)
        assert chosen.status(now=108, lag_rising=False) == (
            "kafka-in healthy and flowing"
        )

    def test_a_zero_poll_interval_is_refused(self):
        with pytest.raises(Invalid):
            ConnectorHealth(name="x", poll_interval=0)
