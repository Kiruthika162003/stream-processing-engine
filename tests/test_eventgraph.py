from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.eventgraph import LineageGraph


def graph() -> LineageGraph:
    built = LineageGraph(scoped_keys={"acct-under-audit"})
    built.record("agg-1", "evt-1", "acct-under-audit")
    built.record("agg-1", "evt-2", "acct-under-audit")
    built.record("agg-2", "agg-1", "acct-under-audit")
    return built


class TestScope:
    def test_out_of_scope_keys_are_not_tracked(self):
        built = graph()
        verdict = built.record("agg-9", "evt-9", "firehose-key")
        assert "out of lineage scope; not tracked" in verdict

    def test_in_scope_contributions_record(self):
        built = graph()
        assert built.record(
            "agg-3", "evt-3", "acct-under-audit"
        ) == "evt-3 -> agg-3 recorded"


class TestTheQueries:
    def test_contributors_trace_backward(self):
        assert graph().contributors_of("agg-1") == [
            "evt-1",
            "evt-2",
        ]

    def test_a_clean_output_has_no_lineage(self):
        with pytest.raises(Invalid):
            graph().contributors_of("agg-clean")

    def test_the_blast_radius_is_the_transitive_closure(self):
        verdict = graph().blast_radius("evt-1")
        assert "evt-1 reached 2 output(s): agg-1, agg-2" in (
            verdict
        )
        assert "the first hop leaves the rest wrong" in verdict

    def test_an_untracked_input_has_no_radius(self):
        with pytest.raises(Invalid):
            graph().blast_radius("evt-ghost")
