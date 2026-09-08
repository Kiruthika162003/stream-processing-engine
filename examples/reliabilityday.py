"""A reliability day: acks, sinks, the dead connector, and the metastable pit.

Run with: python -m examples.reliabilityday
"""

from __future__ import annotations

from rill.acktracking import AckTracker
from rill.connectorhealth import ConnectorHealth
from rill.metastable import MetastableSystem
from rill.retrystorm import RetryStorm
from rill.sinkcontract import SinkContract


def morning_the_acks():
    tracker = AckTracker()
    tracker.emit_root("order-1", children=2, now=0)
    tracker.ack("order-1", new_children=0, now=1)
    verdict = tracker.ack("order-1", new_children=0, now=2)
    print(f"acks:      {verdict}")


def midday_the_sink():
    sink = SinkContract(name="ledger", semantics="idempotent")
    sink.write("txn-1", "v")
    verdict = sink.write("txn-1", "v")
    print(f"sink:      {verdict}")


def afternoon_the_connector():
    connector = ConnectorHealth(name="kafka-in", poll_interval=10)
    connector.heartbeat(now=100, found_data=True)
    print(f"connector: {connector.status(now=200, lag_rising=True).split(';')[0]}")


def dusk_the_storm():
    storm = RetryStorm(
        base_rate=1000, failure_rate=0.8, retry_budget_share=0.1
    )
    print(f"storm:     {storm.comparison(10).split(';')[0]}")


def night_the_pit():
    system = MetastableSystem(
        healthy_threshold=100, amplification=1.5
    )
    system.offer(250)
    system.offer(0)
    print(f"pit:       {system.shed_to(150).split(';')[0]}")
    print(f"           {system.shed_to(80).split(';')[0]}")


def main() -> int:
    morning_the_acks()
    midday_the_sink()
    afternoon_the_connector()
    dusk_the_storm()
    night_the_pit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
