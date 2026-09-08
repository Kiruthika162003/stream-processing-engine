"""Run-length encoding: a column of long runs shrinks, a shuffled one pays a penalty.

A columnar store keeps each field as its own array, and a field
of low cardinality, a status, a category, a boolean, repeats the
same value for long stretches when the column is sorted or
naturally clustered. Run-length encoding replaces each stretch
with the value and a count, so a thousand identical entries
become one pair, and the compression on such a column is
enormous. The catch is that the win depends entirely on the runs
being long, and the runs depend on the order. Sort or cluster the
column and the values gather into a handful of long runs;
shuffle the same values and every neighbor differs, so each entry
becomes its own run of length one, and the encoding stores a
value and a count where the raw stored just a value, an expansion
rather than a compression. So run-length encoding is not a
property of the data's cardinality but of its ordering, which is
why columnar engines sort by the low-cardinality columns they
mean to run-length encode. This module encodes and decodes, and
counts the runs, so the compression, and the penalty when the
order is wrong, are measured against the raw element count.
"""

from __future__ import annotations

from rill.errors import Invalid


def encode(values: list[str]) -> list[tuple[str, int]]:
    if not values:
        raise Invalid("nothing to encode")
    runs: list[tuple[str, int]] = []
    current = values[0]
    length = 1
    for value in values[1:]:
        if value == current:
            length += 1
        else:
            runs.append((current, length))
            current = value
            length = 1
    runs.append((current, length))
    return runs


def decode(runs: list[tuple[str, int]]) -> list[str]:
    out: list[str] = []
    for value, length in runs:
        if length < 1:
            raise Invalid("run length must be positive")
        out.extend([value] * length)
    return out


def run_count(values: list[str]) -> int:
    return len(encode(values))
