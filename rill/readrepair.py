"""Read repair: a read that finds a stale replica fixes it on the way past.

Quorum reads survive a minority of stale replicas by taking the
newest version among the ones they reach, but taking the newest
answer does nothing for the replica that gave the stale one: it
stays stale, and every future read unlucky enough to hit it and
not enough fresher replicas keeps seeing old data until some
write happens to overwrite it, which for a cold key may be never.
Read repair closes that by turning the read into a repair
opportunity. The coordinator gathers the versioned answers, picks
the highest version as the winner, returns it, and then writes
that winning value back to exactly the replicas that answered
with an older version, so the divergence the read exposed is
healed by the read itself. The cost is extra writes to the
laggards on a divergent read, and the benefit is that replicas
converge under read traffic alone without waiting for a write or
a background repair sweep. This module gathers the answers, names
the winner, and lists the replicas that need the repair, so the
convergence is a computed set rather than a promise.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Invalid


@dataclass(frozen=True)
class ReadResult:
    value: str
    version: int
    repairs: tuple[str, ...]


def read_repair(answers: dict[str, tuple[str, int]]) -> ReadResult:
    if not answers:
        raise Invalid("no replicas answered")
    winner_node = max(answers, key=lambda node: answers[node][1])
    value, version = answers[winner_node]
    repairs = tuple(
        sorted(node for node, (_, ver) in answers.items() if ver < version)
    )
    return ReadResult(value=value, version=version, repairs=repairs)


def diverged(answers: dict[str, tuple[str, int]]) -> bool:
    versions = {ver for _, ver in answers.values()}
    return len(versions) > 1
