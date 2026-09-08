"""Edit distance: the fewest single-character edits to turn one string into another.

The Levenshtein distance is the minimum number of single-character
insertions, deletions, and substitutions that transform one string
into another, and it measures how different two strings are in a
way that tolerates typos, drift, and small reorderings, which is
why it backs spell-checkers, fuzzy matching, and near-duplicate
detection. The dynamic program fills a table over prefixes: the
cost to align the first i characters of one string with the first
j of the other is, when those characters match, the cost of
aligning the shorter prefixes, and when they differ, one plus the
cheapest of three moves, delete from the left, insert from the
right, or substitute, which advance one or both prefixes. The
table's corner is the distance, computed in the product of the two
lengths. The subtlety worth stating is that substitution is a
single edit, not two: treating a changed character as a delete
plus an insert would overcount every substitution and inflate the
distance, so the three-way minimum with substitution as one move
is what makes the metric count edits the way a person would. This
module computes the distance, checked on the identities that make
it a metric, so the count is a measured number rather than an
approximate sense of how far apart two strings sit.
"""

from __future__ import annotations

from rill.errors import Invalid


def edit_distance(left: str, right: str) -> int:
    if left is None or right is None:
        raise Invalid("strings must not be None")
    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            if left_char == right_char:
                current.append(previous[j - 1])
            else:
                current.append(
                    1 + min(previous[j], current[j - 1], previous[j - 1])
                )
        previous = current
    return previous[-1]
