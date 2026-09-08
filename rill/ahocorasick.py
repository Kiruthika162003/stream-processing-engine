"""Aho-Corasick: matching many patterns in one pass, with failure links between them.

Searching a text for many patterns at once by running a
single-pattern search per pattern costs the text length times the
pattern count, re-scanning the whole text for each. Aho-Corasick
scans the text once. It builds a trie of all the patterns so
shared prefixes are walked together, and then adds failure links,
the multi-pattern generalization of KMP's failure function: from
each trie node, the failure link points to the node spelling the
longest proper suffix of the path to it that is also a prefix of
some pattern, so on a mismatch the search slides to the longest
still-viable partial match instead of restarting. Following goto
edges where the text matches and failure links where it does not,
the search visits each text character once and reports every
pattern occurrence, including patterns that are suffixes of others
that end at the same position, which the output links propagated
along the failures collect. So a set of a thousand patterns is
found in a single linear pass rather than a thousand passes, which
is why it backs intrusion signatures, keyword filters, and
dictionary matching. This module builds the automaton and reports
every match with its start position, checked against a brute-force
search of each pattern, so the one-pass multi-match is correct as
well as linear.
"""

from __future__ import annotations

from collections import deque

from rill.errors import Invalid


class AhoCorasick:
    def __init__(self, patterns: list[str]) -> None:
        if not patterns or any(not p for p in patterns):
            raise Invalid("patterns must be a non-empty list of non-empty strings")
        self._goto: list[dict[str, int]] = [{}]
        self._out: list[list[str]] = [[]]
        self._fail: list[int] = [0]
        for pattern in patterns:
            node = 0
            for char in pattern:
                if char not in self._goto[node]:
                    self._goto.append({})
                    self._out.append([])
                    self._fail.append(0)
                    self._goto[node][char] = len(self._goto) - 1
                node = self._goto[node][char]
            self._out[node].append(pattern)
        self._build_failures()

    def _build_failures(self) -> None:
        queue: deque[int] = deque()
        for child in self._goto[0].values():
            self._fail[child] = 0
            queue.append(child)
        while queue:
            node = queue.popleft()
            for char, child in self._goto[node].items():
                queue.append(child)
                fallback = self._fail[node]
                while fallback != 0 and char not in self._goto[fallback]:
                    fallback = self._fail[fallback]
                target = self._goto[fallback].get(char, 0)
                self._fail[child] = 0 if target == child else target
                self._out[child] = self._out[child] + self._out[self._fail[child]]

    def find_all(self, text: str) -> list[tuple[int, str]]:
        node = 0
        results: list[tuple[int, str]] = []
        for index, char in enumerate(text):
            while node != 0 and char not in self._goto[node]:
                node = self._fail[node]
            node = self._goto[node].get(char, 0)
            for pattern in self._out[node]:
                results.append((index - len(pattern) + 1, pattern))
        return results
