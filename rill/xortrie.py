"""XOR trie: find the stored number that maximizes XOR with a query, bit by bit.

Given a set of integers, the number in it whose exclusive-or with a
query is largest is a question that comes up in maximum-XOR-pair and
maximum-XOR-subarray problems. Comparing the query against every
stored number is linear per query, quadratic to find the best pair
over a whole set. A binary trie answers each query in time
proportional to the bit width instead, independent of how many
numbers are stored. The trie stores each number as a root-to-leaf
path of its bits from the most significant down, one node per bit,
branching left for a zero and right for a one. To maximize the XOR
with a query, walk down from the most significant bit greedily always
trying to take the branch opposite the query's current bit, because a
differing bit contributes a one to the XOR at that position and a
higher bit outweighs every lower bit combined. When the opposite
branch exists, take it and bank the set bit; when it does not, follow
the same-bit branch, which contributes zero there but keeps the walk
alive for the lower bits. The greedy choice is optimal precisely
because of positional weight: securing a one at a higher bit is worth
more than anything achievable below it, so there is never a reason to
concede a high bit to chase low ones. The finding worth stating is
that the most-significant-first greedy walk gives the true maximum,
not an approximation, and it turns a linear scan per query into a
fixed bit-width walk. This module inserts numbers and queries the
maximum XOR partner, and a test checks the result against the brute
best-over-all-stored answer, so the greedy walk is confirmed optimal.
"""

from __future__ import annotations

from rill.errors import Invalid


class XorTrie:
    def __init__(self, bits: int = 31) -> None:
        if bits <= 0:
            raise Invalid("bit width must be positive")
        self._bits = bits
        self._children: list[list[int]] = [[-1, -1]]

    def insert(self, value: int) -> None:
        if value < 0 or value >= (1 << self._bits):
            raise Invalid("value does not fit in the trie's bit width")
        node = 0
        for i in range(self._bits - 1, -1, -1):
            bit = (value >> i) & 1
            if self._children[node][bit] == -1:
                self._children[node][bit] = len(self._children)
                self._children.append([-1, -1])
            node = self._children[node][bit]

    def max_xor(self, query: int) -> int:
        if not self._has_any():
            raise Invalid("the trie is empty")
        if query < 0 or query >= (1 << self._bits):
            raise Invalid("query does not fit in the trie's bit width")
        node = 0
        result = 0
        for i in range(self._bits - 1, -1, -1):
            bit = (query >> i) & 1
            opposite = 1 - bit
            if self._children[node][opposite] != -1:
                result |= 1 << i
                node = self._children[node][opposite]
            else:
                node = self._children[node][bit]
        return result

    def _has_any(self) -> bool:
        return self._children[0][0] != -1 or self._children[0][1] != -1
