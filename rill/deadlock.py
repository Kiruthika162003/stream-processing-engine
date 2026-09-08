"""Deadlock detection: a cycle in the wait-for graph is a standstill nobody escapes.

Transactions that take locks can wait on each other, and when the
waiting forms a cycle, each holding what the next one needs, none
can proceed and none will ever release, a deadlock that no timeout
alone diagnoses because from inside it every transaction is merely
waiting, which looks the same as being slow. The wait-for graph
makes it detectable: draw an edge from each transaction to the one
it is blocked on, and a cycle in that graph is a deadlock, a
closed loop of dependencies with no exit. Detection is a cycle
search, and resolution is choosing a victim on the cycle to abort,
releasing its locks so the rest can advance, with the victim
usually the youngest or the one holding the least work so the
rollback is cheapest. The distinction that matters is between a
long wait and a cyclic one: a transaction waiting on a chain that
eventually reaches a running transaction will proceed, while one
waiting on a cycle never will, and only the graph tells them
apart. This module builds the wait-for graph, finds a cycle if one
exists, and names a victim to break it, so a deadlock is a
detected structure rather than a set of transactions hung until
someone notices.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class WaitForGraph:
    _waits: dict[str, set[str]] = field(default_factory=dict)

    def wait(self, waiter: str, holder: str) -> None:
        if waiter == holder:
            raise Invalid("a transaction cannot wait on itself")
        self._waits.setdefault(waiter, set()).add(holder)
        self._waits.setdefault(holder, set())

    def resolve(self, waiter: str, holder: str) -> None:
        self._waits.get(waiter, set()).discard(holder)

    def find_cycle(self) -> list[str]:
        color: dict[str, int] = {}
        stack: list[str] = []

        def visit(node: str) -> list[str]:
            color[node] = 1
            stack.append(node)
            for nxt in sorted(self._waits.get(node, set())):
                if color.get(nxt, 0) == 1:
                    return stack[stack.index(nxt):]
                if color.get(nxt, 0) == 0:
                    found = visit(nxt)
                    if found:
                        return found
            stack.pop()
            color[node] = 2
            return []

        for node in sorted(self._waits):
            if color.get(node, 0) == 0:
                cycle = visit(node)
                if cycle:
                    return cycle
        return []

    def deadlocked(self) -> bool:
        return bool(self.find_cycle())

    def victim(self) -> str:
        cycle = self.find_cycle()
        if not cycle:
            raise Invalid("no deadlock; there is no victim to choose")
        return max(cycle)
