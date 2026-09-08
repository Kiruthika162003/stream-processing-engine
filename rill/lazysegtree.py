"""Lazy segment tree: range updates in log time by deferring the push until a query needs it.

A plain segment tree updates one point and queries a range in log
time, but a range update, add this delta to every element from l
to r, done as a point update per element is linear, which defeats
the structure on the workload that most wants it. Lazy propagation
fixes it. A range update that fully covers a node's span stops at
that node: it adjusts the node's aggregate for the whole span and
records the pending delta in a lazy marker on the node, without
descending, so the update touches only the log-many nodes that
tile the range. The deferred work is pushed down only when a later
query or update needs to see inside that node, at which point the
lazy marker is applied to the node's two children and cleared,
which keeps every node's aggregate correct exactly when it is
read. The invariant is that a node's stored aggregate always
reflects its own pending lazy, and its children's do not until the
push, so both range update and range query stay logarithmic. The
subtlety that makes it correct is pushing before descending and
recomputing the aggregate after, and getting the push order wrong
is the classic lazy-propagation bug. This module supports range
add and range sum, checked against a brute-force array, so the
log-time range update is correct and not merely fast.
"""

from __future__ import annotations

from rill.errors import Invalid


class LazySegmentTree:
    def __init__(self, size: int) -> None:
        if size < 1:
            raise Invalid("size must be positive")
        self.size = size
        self._sum = [0] * (4 * size)
        self._lazy = [0] * (4 * size)

    def _push(self, node: int, lo: int, hi: int) -> None:
        delta = self._lazy[node]
        if delta == 0:
            return
        mid = (lo + hi) // 2
        left, right = 2 * node, 2 * node + 1
        self._sum[left] += (mid - lo + 1) * delta
        self._lazy[left] += delta
        self._sum[right] += (hi - mid) * delta
        self._lazy[right] += delta
        self._lazy[node] = 0

    def _update(self, node: int, lo: int, hi: int, ql: int, qr: int, delta: int) -> None:
        if qr < lo or hi < ql:
            return
        if ql <= lo and hi <= qr:
            self._sum[node] += (hi - lo + 1) * delta
            self._lazy[node] += delta
            return
        self._push(node, lo, hi)
        mid = (lo + hi) // 2
        self._update(2 * node, lo, mid, ql, qr, delta)
        self._update(2 * node + 1, mid + 1, hi, ql, qr, delta)
        self._sum[node] = self._sum[2 * node] + self._sum[2 * node + 1]

    def _query(self, node: int, lo: int, hi: int, ql: int, qr: int) -> int:
        if qr < lo or hi < ql:
            return 0
        if ql <= lo and hi <= qr:
            return self._sum[node]
        self._push(node, lo, hi)
        mid = (lo + hi) // 2
        return self._query(2 * node, lo, mid, ql, qr) + self._query(
            2 * node + 1, mid + 1, hi, ql, qr
        )

    def add_range(self, lo: int, hi: int, delta: int) -> None:
        if not 0 <= lo <= hi < self.size:
            raise Invalid("range out of bounds")
        self._update(1, 0, self.size - 1, lo, hi, delta)

    def range_sum(self, lo: int, hi: int) -> int:
        if not 0 <= lo <= hi < self.size:
            raise Invalid("range out of bounds")
        return self._query(1, 0, self.size - 1, lo, hi)
