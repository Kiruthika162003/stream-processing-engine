from __future__ import annotations

import pytest

from rill.errors import Invalid, Missing
from rill.sessionguarantees import Session


class TestMonotonicReads:
    def test_a_read_advances_the_seen_version(self):
        session = Session()
        assert session.read(5) == 5
        assert session.seen() == 5

    def test_a_read_from_a_lagging_replica_is_refused(self):
        session = Session()
        session.read(10)
        with pytest.raises(Missing) as caught:
            session.read(7)
        assert "route to a fresher replica" in str(caught.value)

    def test_a_read_at_or_past_the_seen_version_is_allowed(self):
        session = Session()
        session.read(10)
        assert session.read(10) == 10
        assert session.read(12) == 12


class TestReadYourWrites:
    def test_a_read_must_see_at_least_the_clients_own_write(self):
        session = Session()
        session.wrote(20)
        with pytest.raises(Missing):
            session.read(15)  # replica has not applied the write yet
        assert session.read(20) == 20


class TestRefusals:
    def test_a_negative_write_version_is_refused(self):
        with pytest.raises(Invalid):
            Session().wrote(-1)

    def test_a_negative_read_version_is_refused(self):
        with pytest.raises(Invalid):
            Session().read(-1)
