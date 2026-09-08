from __future__ import annotations

from rill.bipartite import greedy_matching, max_matching


class TestGreedyStrands:
    def test_augmenting_beats_greedy_when_a_task_has_one_option(self):
        # t2 can only use W; greedy gives W to t1 and strands t2
        edges = {"t1": ["W", "X"], "t2": ["W"]}
        assert max_matching(edges) == 2
        assert greedy_matching(edges) == 1

    def test_a_larger_contended_case(self):
        edges = {"a": ["W", "X"], "b": ["W", "Y"], "c": ["W"]}
        assert max_matching(edges) == 3
        assert greedy_matching(edges) == 2


class TestBasics:
    def test_disjoint_tasks_all_match(self):
        edges = {"a": ["W"], "b": ["X"], "c": ["Y"]}
        assert max_matching(edges) == 3

    def test_more_tasks_than_workers_caps_at_the_workers(self):
        edges = {"a": ["W"], "b": ["W"], "c": ["W"]}
        assert max_matching(edges) == 1

    def test_no_edges_matches_nothing(self):
        assert max_matching({}) == 0

    def test_a_task_with_no_workers_stays_unmatched(self):
        assert max_matching({"a": [], "b": ["W"]}) == 1
