"""Trie: prefix lookup in the length of the key, not the size of the dictionary.

Routing by topic prefix, completing a partial term, matching a
subscription pattern all ask the same question: which stored keys
start with this string. A hash set answers exact membership but
cannot answer prefixes without scanning every key. A trie stores
the keys as a tree of characters, each path from the root
spelling a prefix, so following a key costs a step per character
and reaching the end tells you whether the key is present, both in
time proportional to the key's length and independent of how many
keys the trie holds. The property that makes it worth the pointers
is the prefix walk: descending to the node that ends a prefix and
then collecting every key beneath it returns all completions in
time proportional to the prefix plus the number of matches, never
touching the keys that do not share the prefix. A shared prefix is
stored once, so a dictionary of keys with common heads is compact
as well as fast to query by head. This module builds the tree,
answers exact membership, and collects the keys under a prefix, so
the length-not-count lookup and the prefix enumeration are tests
rather than asymptotic claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class _Node:
    children: dict[str, _Node] = field(default_factory=dict)
    terminal: bool = False


@dataclass
class Trie:
    _root: _Node = field(default_factory=_Node)

    def add(self, word: str) -> None:
        if not word:
            raise Invalid("cannot add an empty string")
        node = self._root
        for character in word:
            node = node.children.setdefault(character, _Node())
        node.terminal = True

    def contains(self, word: str) -> bool:
        node = self._descend(word)
        return node is not None and node.terminal

    def _descend(self, prefix: str) -> _Node | None:
        node = self._root
        for character in prefix:
            nxt = node.children.get(character)
            if nxt is None:
                return None
            node = nxt
        return node

    def with_prefix(self, prefix: str) -> list[str]:
        node = self._descend(prefix)
        if node is None:
            return []
        found: list[str] = []
        self._collect(node, prefix, found)
        return sorted(found)

    def _collect(self, node: _Node, prefix: str, out: list[str]) -> None:
        if node.terminal:
            out.append(prefix)
        for character, child in node.children.items():
            self._collect(child, prefix + character, out)
