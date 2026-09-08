"""Longest common subsequence: how much of two sequences aligns, in order, with gaps allowed.

Comparing two sequences for how much they share in order, two
event streams that should agree, two versions of a log, a diff
between runs, is the longest common subsequence: the longest
sequence of elements appearing in both, in the same order but not
necessarily adjacent. It is not the longest common substring,
which requires contiguity, and the difference matters because a
subsequence tolerates insertions and deletions between the matched
elements, which is exactly what a diff or an alignment must do.
The dynamic program fills a table indexed by prefixes of the two
sequences: at each cell, if the two current elements match, the
LCS extends the alignment of the shorter prefixes by one, and if
they do not, it keeps the better of dropping one element from
either side. The table's far corner is the answer, computed in the
product of the two lengths, and the same table reconstructs the
aligned subsequence itself by walking back through the choices.
LCS underlies the diff that shows what changed between two
versions, because the elements not on the longest common
subsequence are precisely the insertions and deletions. This
module computes the length and the aligned subsequence, so the
alignment is a result rather than an eyeballed guess at what two
sequences have in common.
"""

from __future__ import annotations

from rill.errors import Invalid


def lcs_length(left: list[str], right: list[str]) -> int:
    return len(lcs(left, right))


def lcs(left: list[str], right: list[str]) -> list[str]:
    if left is None or right is None:
        raise Invalid("sequences must not be None")
    rows, cols = len(left), len(right)
    table = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            if left[i - 1] == right[j - 1]:
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])
    result: list[str] = []
    i, j = rows, cols
    while i > 0 and j > 0:
        if left[i - 1] == right[j - 1]:
            result.append(left[i - 1])
            i -= 1
            j -= 1
        elif table[i - 1][j] >= table[i][j - 1]:
            i -= 1
        else:
            j -= 1
    result.reverse()
    return result
