"""Snowflake IDs: time-sortable unique ids, and the two ways a clock betrays them.

A distributed id generator wants three things at once: uniqueness
across nodes, no coordination on the hot path, and ids that sort
by creation time. Snowflake packs all three into one integer, the
high bits a millisecond timestamp, the middle bits a node id, the
low bits a per-millisecond sequence, so two nodes never collide,
no node asks anyone before minting, and the numeric order of the
ids is their time order. The scheme rests entirely on the clock,
and the clock betrays it in two ways the generator must handle
rather than ignore. Within a single millisecond the sequence bits
are finite, so a node minting faster than the sequence can count
must wait for the next millisecond rather than wrap and collide.
And a clock that steps backward, an NTP correction say, would mint
ids that sort before ids already handed out and could duplicate
them, so a backward step is refused outright, not papered over.
This module packs the id, advances the sequence within a
millisecond, forces the wait when the sequence is spent, and
rejects a retreating clock, so both betrayals are handled where
they happen.
"""

from __future__ import annotations

from dataclasses import dataclass

from rill.errors import Halted, Invalid

NODE_BITS = 10
SEQ_BITS = 12
MAX_NODE = (1 << NODE_BITS) - 1
MAX_SEQ = (1 << SEQ_BITS) - 1


@dataclass
class SnowflakeGenerator:
    node_id: int
    epoch: int = 0
    _last_ms: int = -1
    _seq: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.node_id <= MAX_NODE:
            raise Invalid(f"node id must be in [0, {MAX_NODE}]")

    def next_id(self, now_ms: int) -> int:
        if now_ms < self._last_ms:
            raise Invalid(
                f"clock went backward from {self._last_ms} to {now_ms}; "
                "refusing to mint ids that sort before ones already issued"
            )
        if now_ms == self._last_ms:
            if self._seq >= MAX_SEQ:
                raise Halted(
                    "sequence exhausted this millisecond; wait for the next"
                )
            self._seq += 1
        else:
            self._seq = 0
            self._last_ms = now_ms
        offset = now_ms - self.epoch
        return (offset << (NODE_BITS + SEQ_BITS)) | (
            self.node_id << SEQ_BITS
        ) | self._seq
