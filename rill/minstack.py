"""Min stack: the minimum of everything on the stack, in constant time, via a second stack.

A stack that can also report the smallest value it currently holds
looks like it needs a scan of its contents per query, O(n), but a
second stack makes the minimum O(1). Alongside the main stack of
values, keep a parallel stack whose top is always the minimum of
everything currently pushed: on a push, append to the min stack
the smaller of the new value and the current minimum, and on a pop,
pop both stacks together. Because each entry in the min stack
records the running minimum as of when its value was pushed,
popping a value automatically restores the minimum that held
before it, with no recomputation. So push, pop, and minimum are
all constant time, and the extra space is one integer per element.
The insight is that the minimum only changes at the boundaries a
push or pop crosses, and storing the minimum-so-far at each level
is exactly enough to recover it as the stack shrinks, which a
single running-minimum variable cannot do because it has no way to
un-see a value that is popped off. This module keeps the two
stacks in lockstep and answers the minimum from the top of the
second, so the constant-time minimum over a mutating stack is a
checkable property rather than a re-scan.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Missing


@dataclass
class MinStack:
    _values: list[int] = field(default_factory=list)
    _mins: list[int] = field(default_factory=list)

    def push(self, value: int) -> None:
        self._values.append(value)
        current_min = value if not self._mins else min(value, self._mins[-1])
        self._mins.append(current_min)

    def pop(self) -> int:
        if not self._values:
            raise Missing("pop from an empty stack")
        self._mins.pop()
        return self._values.pop()

    def minimum(self) -> int:
        if not self._mins:
            raise Missing("no minimum of an empty stack")
        return self._mins[-1]

    def __len__(self) -> int:
        return len(self._values)
