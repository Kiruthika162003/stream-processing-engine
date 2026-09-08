from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.unionfind import UnionFind


def _tournament(compress: bool) -> UnionFind:
    uf = UnionFind(compress=compress)
    nodes = [str(number) for number in range(64)]
    for node in nodes:
        uf.add(node)
    level = nodes[:]
    while len(level) > 1:
        nxt = []
        for index in range(0, len(level) - 1, 2):
            uf.union(level[index], level[index + 1])
            nxt.append(uf.find(level[index]))
        if len(level) % 2:
            nxt.append(level[-1])
        level = nxt
    return uf


class TestComponents:
    def test_merging_everything_leaves_one_component(self):
        uf = _tournament(compress=True)
        assert uf.components() == 1

    def test_separate_merges_stay_separate(self):
        uf = UnionFind()
        uf.union("a", "b")
        uf.union("c", "d")
        assert uf.connected("a", "b")
        assert not uf.connected("a", "c")
        assert uf.components() == 2


class TestCompression:
    def test_without_compression_the_walk_stays_at_the_depth(self):
        uf = _tournament(compress=False)
        uf.find("63")
        assert uf.last_walk() == 6
        uf.find("63")
        assert uf.last_walk() == 6

    def test_compression_flattens_the_repeat_find(self):
        uf = _tournament(compress=True)
        uf.find("63")
        first = uf.last_walk()
        uf.find("63")
        second = uf.last_walk()
        assert first == 6
        assert second == 1


class TestRefusals:
    def test_finding_an_unknown_element_is_refused(self):
        with pytest.raises(Invalid):
            UnionFind().find("ghost")
