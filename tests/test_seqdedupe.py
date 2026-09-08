from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.seqdedupe import ACCEPTED, DUPLICATE, SequenceBroker


class TestAcceptance:
    def test_the_next_sequence_is_accepted(self):
        broker = SequenceBroker()
        assert broker.write("p", 0, "a") == ACCEPTED
        assert broker.write("p", 1, "b") == ACCEPTED
        assert broker.last_accepted("p") == 1

    def test_producers_keep_separate_sequences(self):
        broker = SequenceBroker()
        broker.write("p", 0, "a")
        assert broker.write("q", 0, "a") == ACCEPTED


class TestRetryIsIdempotent:
    def test_a_replayed_sequence_is_a_duplicate_not_a_write(self):
        broker = SequenceBroker()
        broker.write("p", 0, "a")
        broker.write("p", 1, "b")
        assert broker.write("p", 1, "b") == DUPLICATE
        assert broker.last_accepted("p") == 1

    def test_an_old_sequence_is_a_duplicate(self):
        broker = SequenceBroker()
        broker.write("p", 0, "a")
        broker.write("p", 1, "b")
        assert broker.write("p", 0, "a") == DUPLICATE


class TestGapIsLoud:
    def test_a_skipped_sequence_is_refused_not_accepted(self):
        broker = SequenceBroker()
        broker.write("p", 0, "a")
        with pytest.raises(Invalid) as caught:
            broker.write("p", 2, "c")
        assert "a record went missing" in str(caught.value)

    def test_a_negative_sequence_is_refused(self):
        broker = SequenceBroker()
        with pytest.raises(Invalid):
            broker.write("p", -1, "a")
