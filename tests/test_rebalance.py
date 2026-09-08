from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.rebalance import ConsumerGroup


def grown_group(protocol: str) -> ConsumerGroup:
    group = ConsumerGroup(protocol=protocol, partitions=30)
    for number in range(1, 7):
        group.join(f"c{number}")
    return group


class TestTheProtocols:
    def test_eager_pauses_all_seven_for_one_arrival(self):
        group = grown_group("eager")
        note = group.join("c7")
        assert note == (
            "eager: every consumer paused for a re-deal that "
            "moved 4 partition(s)"
        )

    def test_incremental_pauses_the_donors_and_the_newcomer(self):
        group = grown_group("incremental")
        note = group.join("c7")
        assert note == (
            "incremental: 5 consumer(s) paused, the rest "
            "never stopped"
        )

    def test_the_leave_shows_the_same_shape(self):
        eager = grown_group("eager")
        eager.join("c7")
        assert "every consumer paused" in eager.leave("c3")
        incremental = grown_group("incremental")
        incremental.join("c7")
        assert "4 consumer(s) paused" in incremental.leave("c3")

    def test_unknown_protocols_are_refused(self):
        with pytest.raises(Invalid) as caught:
            ConsumerGroup(protocol="polite", partitions=4)
        assert "strength of being the default" in str(
            caught.value
        )


class TestTheStickyDeal:
    def test_the_newcomer_is_not_starved(self):
        group = grown_group("incremental")
        group.join("c7")
        loads: dict[str, int] = {}
        for holder in group.assignment.values():
            loads[holder] = loads.get(holder, 0) + 1
        assert loads["c7"] == 4
        assert max(loads.values()) - min(loads.values()) <= 1

    def test_membership_is_checked_both_ways(self):
        group = grown_group("eager")
        with pytest.raises(Invalid):
            group.join("c1")
        with pytest.raises(Invalid):
            group.leave("ghost")

    def test_the_bill_totals_the_pause_events(self):
        group = grown_group("incremental")
        group.join("c7")
        group.leave("c3")
        assert group.pause_bill().startswith(
            "incremental: 30 pause event(s) across 7 "
            "consumer(s)"
        )
