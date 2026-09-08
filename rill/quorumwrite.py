"""Quorum writes: durability without waiting for the slowest replica.

Writing state to replicas for durability poses the latency
question every distributed store answers: wait for all
replicas and inherit the slowest one's tail latency, or wait
for one and risk losing the write when that one dies before it
replicates. Quorum is the middle, wait for a majority, which
survives a minority failing and does not wait on the slowest,
and the arithmetic that makes it correct is that read and
write quorums must overlap, so a read always sees the latest
committed write. The module computes the quorum from the
replica count and checks the overlap invariant, refusing a
configuration where read and write quorums can miss each
other, because that configuration returns stale reads that
look exactly like fresh ones. The latency it reports is the
k-th fastest replica, not the slowest, since that is the
actual wait a quorum write incurs, and the difference between
the slowest and the k-th fastest is what quorum buys.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class QuorumConfig:
    replicas: int
    write_quorum: int
    read_quorum: int

    def __post_init__(self) -> None:
        if self.replicas < 1:
            raise Invalid("a store needs replicas")
        for name, value in (
            ("write", self.write_quorum),
            ("read", self.read_quorum),
        ):
            if not 1 <= value <= self.replicas:
                raise Invalid(
                    f"the {name} quorum must be between 1 and "
                    f"{self.replicas}"
                )
        if self.write_quorum + self.read_quorum <= self.replicas:
            raise Invalid(
                f"write {self.write_quorum} + read "
                f"{self.read_quorum} <= {self.replicas}: the "
                "quorums can miss each other and return a stale "
                "read that looks exactly like a fresh one"
            )

    def tolerates_failures(self) -> int:
        return self.replicas - self.write_quorum

    def write_latency(self, replica_latencies: list[int]) -> str:
        if len(replica_latencies) != self.replicas:
            raise Invalid(
                "one latency per replica, no more, no less"
            )
        ordered = sorted(replica_latencies)
        quorum_wait = ordered[self.write_quorum - 1]
        slowest = ordered[-1]
        return (
            f"quorum write waits {quorum_wait} (the "
            f"{self.write_quorum}th fastest), not {slowest} "
            f"(the slowest); quorum buys the {slowest - quorum_wait} "
            "tick difference"
        )

    def overlap_note(self) -> str:
        overlap = (
            self.write_quorum + self.read_quorum - self.replicas
        )
        return (
            f"read and write quorums overlap by {overlap} "
            f"replica(s), tolerating {self.tolerates_failures()} "
            "write failure(s); the overlap is why a read always "
            "sees the latest write"
        )
