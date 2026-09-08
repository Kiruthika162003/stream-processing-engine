"""Source connector health: the input that stopped without saying so.

A pipeline's most invisible failure is a source connector that
silently stops pulling, because everything downstream looks
healthy, it is simply processing nothing, and a graph of zero
throughput looks identical to a genuinely quiet Tuesday. The
health check distinguishes the two the only way possible, by
what the source itself knows: a connector polling and getting
empty responses is healthy and idle, while a connector whose
poll loop has died is not polling at all, and the difference
is a heartbeat the poll loop emits whether or not it found
data. The check watches heartbeat freshness against poll
interval, not throughput, because throughput conflates a
dead connector with a quiet source, and a connector that
stopped emitting heartbeats has stopped running even if its
last data looked recent. The lag-versus-idle verdict is the
payoff: rising lag with a fresh heartbeat is a slow consumer,
rising lag with a stale heartbeat is a dead source, and they
send the operator to opposite ends of the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class ConnectorHealth:
    name: str
    poll_interval: int
    last_heartbeat: int = 0
    last_data: int = 0

    def __post_init__(self) -> None:
        if self.poll_interval < 1:
            raise Invalid("a poll interval is positive")

    def heartbeat(self, now: int, found_data: bool) -> None:
        self.last_heartbeat = now
        if found_data:
            self.last_data = now

    def status(self, now: int, lag_rising: bool) -> str:
        heartbeat_age = now - self.last_heartbeat
        alive = heartbeat_age <= self.poll_interval * 2
        if not alive:
            return (
                f"{self.name} DEAD: no heartbeat for "
                f"{heartbeat_age}, poll loop stopped; not a "
                "quiet source, a dead connector, however "
                "recent its last data looks"
            )
        if lag_rising:
            return (
                f"{self.name} alive but lag rising: a slow "
                "consumer, not a dead source; look downstream, "
                "not at the connector"
            )
        if now - self.last_data > self.poll_interval * 3:
            return (
                f"{self.name} healthy and idle: polling, "
                "getting empty responses, a genuinely quiet "
                "source and not a failure"
            )
        return f"{self.name} healthy and flowing"
