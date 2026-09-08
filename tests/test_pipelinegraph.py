from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.pipelinegraph import PipelineGraph


def diamond() -> PipelineGraph:
    graph = PipelineGraph()
    for name in ("source", "left", "right", "sink"):
        graph.add_operator(name)
    graph.wire("source", "left")
    graph.wire("source", "right")
    graph.wire("left", "sink")
    graph.wire("right", "sink")
    return graph


class TestWiring:
    def test_a_wire_connects_operators(self):
        graph = diamond()
        assert "source" in graph.upstreams["left"]

    def test_a_cycle_is_refused_with_the_loop_named(self):
        graph = diamond()
        with pytest.raises(Invalid) as caught:
            graph.wire("sink", "source")
        assert "closes a cycle" in str(caught.value)
        assert "running out of memory" in str(caught.value)

    def test_wiring_an_unknown_operator_is_refused(self):
        graph = diamond()
        with pytest.raises(Invalid):
            graph.wire("ghost", "sink")

    def test_double_adding_an_operator_is_refused(self):
        graph = diamond()
        with pytest.raises(Invalid):
            graph.add_operator("sink")


class TestClosures:
    def test_the_upstream_closure_is_everything_before(self):
        assert diamond().upstream_closure("sink") == {
            "source",
            "left",
            "right",
        }

    def test_the_downstream_closure_is_the_blast_radius(self):
        assert diamond().downstream_closure("source") == {
            "left",
            "right",
            "sink",
        }

    def test_a_leaf_has_no_downstream(self):
        assert diamond().downstream_closure("sink") == set()


class TestTopologicalOrder:
    def test_upstreams_come_before_downstreams(self):
        order = diamond().topological_order()
        assert order.index("source") < order.index("left")
        assert order.index("left") < order.index("sink")
        assert order.index("right") < order.index("sink")
