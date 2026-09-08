from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.offsets import OffsetConsumer, crash_drill


class TestTheDial:
    def test_the_dial_has_two_settings(self):
        with pytest.raises(Invalid) as caught:
            OffsetConsumer(policy="exactly-once")
        assert "only dedupe on top" in str(caught.value)

    def test_consumers_read_in_order_or_not_at_all(self):
        consumer = OffsetConsumer(policy="process-first")
        consumer.consume(0)
        with pytest.raises(Invalid):
            consumer.consume(5)


class TestTheCrash:
    def test_commit_first_tells_the_quiet_lie(self):
        consumer = OffsetConsumer(policy="commit-first")
        consumer.consume(0)
        verdict = consumer.crash_during(1)
        assert "never happens, the quiet lie" in verdict
        assert consumer.resume_from() == 2

    def test_process_first_tells_the_loud_lie(self):
        consumer = OffsetConsumer(policy="process-first")
        consumer.consume(0)
        verdict = consumer.crash_during(1)
        assert "happens again, the loud lie" in verdict
        assert consumer.resume_from() == 1


class TestTheDrill:
    def test_both_numbers_land_on_one_page(self):
        page = crash_drill(tape_length=10, crash_at=4)
        assert page == (
            "one tape, one crash at 4: commit-first processed "
            "9 of 10 and lost 1; process-first processed "
            "everything and repeated 1; the two numbers that "
            "end the abstract argument"
        )

    def test_the_crash_must_land_on_the_tape(self):
        with pytest.raises(Invalid):
            crash_drill(tape_length=5, crash_at=9)
