"""A coordination day: counters merge, sets settle, clocks disagree, a commit waits.

Run with: python -m examples.coordinationday
"""

from __future__ import annotations

from rill.crdtcounter import GCounter
from rill.orset import ORSet
from rill.raftcommit import RaftLeader
from rill.twophase import TwoPhaseCoordinator
from rill.vectorclock import VectorClock, compare


def morning_the_counter():
    alice = GCounter("a")
    alice.increment(3)
    bob = GCounter("b")
    bob.increment(5)
    alice.merge(bob)
    print(f"counter:  concurrent 3 and 5 merged to {alice.value()}")


def midday_the_set():
    alice = ORSet()
    alice.add("x", "t1")
    bob = ORSet()
    bob.merge(alice)
    alice.remove("x")
    bob.add("x", "t2")
    alice.merge(bob)
    print(f"orset:    concurrent add survives remove: {alice.contains('x')}")


def afternoon_the_clock():
    left = VectorClock("a").tick()
    right = VectorClock("b").tick()
    print(f"clock:    independent ticks are {compare(left, right)}")


def dusk_the_raft():
    leader = RaftLeader(servers=3, current_term=2)
    leader.append(1)
    leader.replicated("f1", 1)
    stranded = leader.commit_index()
    leader.append(2)
    leader.replicated("f1", 2)
    print(f"raft:     prior-term commit {stranded}, then {leader.commit_index()}")


def night_the_commit():
    coord = TwoPhaseCoordinator(participants=("a", "b"))
    coord.vote("a", True)
    blocked = coord.blocked()
    coord.vote("b", True)
    coord.decide()
    print(f"2pc:      blocked {blocked}, decided {coord.outcome('a')}")


def main() -> int:
    morning_the_counter()
    midday_the_set()
    afternoon_the_clock()
    dusk_the_raft()
    night_the_commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
