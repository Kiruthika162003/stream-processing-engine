from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.priority import PriorityLanes


def flooded() -> PriorityLanes:
    lanes = PriorityLanes(express_per_standard=3)
    for number in range(30):
        lanes.enqueue(f"fraud-{number}", "express")
    for number in range(5):
        lanes.enqueue(f"ping-{number}", "standard")
    return lanes


class TestTheLanes:
    def test_express_drains_first(self):
        lanes = PriorityLanes(express_per_standard=3)
        lanes.enqueue("ping-1", "standard")
        lanes.enqueue("fraud-1", "express")
        assert lanes.drain_one() == "express: fraud-1"

    def test_guessed_urgency_is_refused(self):
        lanes = PriorityLanes(express_per_standard=2)
        with pytest.raises(Invalid) as caught:
            lanes.enqueue("e", "looks-small")
        assert "not guessed from size or smell" in str(
            caught.value
        )


class TestStarvation:
    def test_the_flood_cannot_starve_the_standard_lane(self):
        lanes = flooded()
        drained = [lanes.drain_one() for _ in range(20)]
        standards = [
            entry for entry in drained if entry.startswith("standard")
        ]
        assert len(standards) == 5
        assert drained[3] == "standard: ping-0"

    def test_the_contract_is_proven_with_counts(self):
        lanes = flooded()
        for _ in range(20):
            lanes.drain_one()
        meter = lanes.contract_meter()
        assert "15 express to 5 standard (3.0:1" in meter
        assert "counts rather than intentions" in meter

    def test_an_empty_drain_returns_none(self):
        lanes = PriorityLanes(express_per_standard=2)
        assert lanes.drain_one() is None
        with pytest.raises(Invalid):
            lanes.contract_meter()

    def test_express_alone_still_drains(self):
        lanes = PriorityLanes(express_per_standard=2)
        for number in range(5):
            lanes.enqueue(f"f{number}", "express")
        drained = [lanes.drain_one() for _ in range(5)]
        assert all(
            entry.startswith("express") for entry in drained
        )
