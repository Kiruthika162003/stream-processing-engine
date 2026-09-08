from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.events import Event
from rill.operators import Chain, FilterEvents, MapValues, Rekey


def at(key: str, value: int, event_time: int = 5) -> Event:
    return Event(
        key=key, value=value, event_time=event_time,
        arrival=event_time,
    )


def pipeline() -> Chain:
    return Chain(
        stages=[
            FilterEvents(
                name="drop-zeroes",
                keep=lambda event: event.value != 0,
                reason="zero readings are sensor hiccups",
            ),
            MapValues(name="double", fn=lambda value: value * 2),
            Rekey(
                name="by-parity",
                route=lambda event: (
                    "even" if event.value % 2 == 0 else "odd"
                ),
            ),
        ]
    )


class TestTheMachines:
    def test_the_map_is_one_in_one_out(self):
        stage = MapValues(name="double", fn=lambda v: v * 2)
        out = stage.process(at("a", 3))
        assert out[0].value == 6
        assert stage.census() == "double: 1 in, 1 out"

    def test_the_filter_must_name_its_reason(self):
        with pytest.raises(Invalid) as caught:
            FilterEvents(
                name="quiet", keep=lambda _e: True, reason=" "
            )
        assert "lookup into an investigation" in str(caught.value)

    def test_the_filter_census_explains_the_shrink(self):
        stage = FilterEvents(
            name="drop-zeroes",
            keep=lambda event: event.value != 0,
            reason="zero readings are sensor hiccups",
        )
        stage.process(at("a", 0))
        stage.process(at("a", 7))
        assert stage.census() == (
            "drop-zeroes: 2 in, 1 out, 1 dropped (zero "
            "readings are sensor hiccups)"
        )

    def test_the_rekey_keeps_a_route_census(self):
        stage = Rekey(
            name="by-parity",
            route=lambda event: (
                "even" if event.value % 2 == 0 else "odd"
            ),
        )
        stage.process(at("a", 2))
        stage.process(at("b", 3))
        stage.process(at("c", 4))
        census = stage.census()
        assert "rerouted to 2 key(s) (even:2, odd:1)" in census

    def test_an_empty_route_is_refused(self):
        stage = Rekey(name="bad", route=lambda _event: "")
        with pytest.raises(Invalid):
            stage.process(at("a", 1))


class TestTheChain:
    def test_the_chain_threads_events_through_in_order(self):
        chain = pipeline()
        out = chain.process(at("a", 3))
        assert len(out) == 1
        assert out[0].key == "even"
        assert out[0].value == 6

    def test_a_dropped_event_stops_early(self):
        chain = pipeline()
        assert chain.process(at("a", 0)) == []

    def test_the_xray_reads_stage_by_stage(self):
        chain = pipeline()
        chain.process(at("a", 3))
        chain.process(at("b", 0))
        xray = chain.xray()
        assert xray.startswith("the pipeline's own X-ray:")
        assert "drop-zeroes: 2 in, 1 out, 1 dropped" in xray
        assert "double: 1 in, 1 out" in xray

    def test_an_empty_chain_is_refused(self):
        with pytest.raises(Invalid):
            Chain(stages=[])
