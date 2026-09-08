"""Acknowledgement tracking: an event is done only when the whole tree of it is.

At-least-once delivery needs the source to know when an event
is fully processed so it can advance its offset, and fully
processed is subtler than it looks, because one input event
can fan out into many downstream events, and the input is done
only when every descendant it spawned has been acknowledged.
The tracker keeps an ack tree per root event: the root is
pending until its children are acked, and a child that spawns
grandchildren stays pending until those are too, so the ack
propagates up only from the leaves. The timeout is the safety
valve, a root whose tree has not fully acked within a deadline
is replayed, which is the at-least-once guarantee in action,
and the tracker distinguishes a slow tree from a lost one by
whether any progress happened, because replaying a tree that
was almost done wastes the work already acked while replaying
a stalled one is the only way to make progress.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class AckTracker:
    pending: dict[str, int] = field(default_factory=dict)
    acked_roots: list[str] = field(default_factory=list)
    replayed: list[str] = field(default_factory=list)
    started_at: dict[str, int] = field(default_factory=dict)
    last_progress: dict[str, int] = field(default_factory=dict)

    def emit_root(self, root_id: str, children: int, now: int) -> str:
        if root_id in self.pending:
            raise Invalid(f"{root_id} already in flight")
        if children < 1:
            raise Invalid(
                "a root with no children is done at birth; "
                "ack it directly instead"
            )
        self.pending[root_id] = children
        self.started_at[root_id] = now
        self.last_progress[root_id] = now
        return f"{root_id} emitted with {children} child(ren) pending"

    def ack(
        self, root_id: str, new_children: int, now: int
    ) -> str:
        if root_id not in self.pending:
            raise Invalid(f"{root_id} is not in flight")
        self.pending[root_id] += new_children - 1
        self.last_progress[root_id] = now
        if self.pending[root_id] <= 0:
            del self.pending[root_id]
            self.acked_roots.append(root_id)
            return (
                f"{root_id} fully acked: every descendant "
                "done, the source may advance its offset"
            )
        return (
            f"{root_id}: {self.pending[root_id]} still pending, "
            "the ack propagates up only from the leaves"
        )

    def sweep_timeouts(self, now: int, deadline: int) -> str:
        replayed_now = []
        for root_id in list(self.pending):
            if now - self.started_at[root_id] > deadline:
                stalled = (
                    now - self.last_progress[root_id] > deadline
                )
                self.replayed.append(root_id)
                replayed_now.append(
                    f"{root_id} ("
                    + ("stalled" if stalled else "slow")
                    + ")"
                )
                del self.pending[root_id]
        if not replayed_now:
            return "no timeouts; every tree progressing"
        return (
            f"replayed {len(replayed_now)}: "
            + ", ".join(replayed_now)
            + "; the at-least-once guarantee in action"
        )
