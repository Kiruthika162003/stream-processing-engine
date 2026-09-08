from __future__ import annotations

import pytest

from rill.branch import StreamBranch
from rill.errors import Invalid
from rill.events import Event


def at(key: str, value: int) -> Event:
    return Event(key=key, value=value, event_time=1, arrival=1)


def wired() -> StreamBranch:
    split = StreamBranch()
    split.add_branch(
        "big", lambda event: event.value >= 100
    )
    split.add_branch(
        "small", lambda event: 0 < event.value < 100
    )
    return split


class TestRouting:
    def test_every_event_takes_exactly_one_door(self):
        split = wired()
        assert split.route(at("a", 500)) == "big"
        assert split.route(at("b", 5)) == "small"

    def test_the_unwanted_event_lands_in_the_default(self):
        split = wired()
        assert split.route(at("c", 0)) == "default"

    def test_duplicate_branch_names_are_refused(self):
        split = wired()
        with pytest.raises(Invalid):
            split.add_branch("big", lambda _event: True)


class TestTheInvariants:
    def test_overlap_is_caught_by_probe_at_wiring_time(self):
        split = wired()
        split.add_branch(
            "positive", lambda event: event.value > 0
        )
        with pytest.raises(Invalid) as caught:
            split.probe_overlap([at("probe", 50)])
        assert "small and positive" in str(caught.value)
        assert "until finance reconciles" in str(caught.value)

    def test_clean_probes_pass(self):
        assert wired().probe_overlap(
            [at("p1", 500), at("p2", 5)]
        ) == "2 probe(s), no overlap"

    def test_the_doors_sum(self):
        split = wired()
        for value in (500, 5, 0, 200, 30):
            split.route(at("k", value))
        audit = split.conservation_audit()
        assert audit.startswith("5 in, 5 out; the doors sum")

    def test_the_fat_default_is_the_loudest_line(self):
        split = wired()
        for value in (0, 0, 0, 500):
            split.route(at("k", value))
        audit = split.conservation_audit()
        assert "the default holds 3 (75%)" in audit
        assert "the first anyone hears of it" in audit
