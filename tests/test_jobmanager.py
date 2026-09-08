from __future__ import annotations

import pytest

from rill.errors import Halted, Invalid
from rill.jobmanager import JobManagerElection


def elected() -> JobManagerElection:
    election = JobManagerElection()
    election.acquire("jm-a", now=0)
    return election


class TestTheLease:
    def test_a_held_lease_makes_candidates_wait(self):
        election = elected()
        with pytest.raises(Invalid):
            election.acquire("jm-b", now=10)

    def test_expiry_transfers_with_a_higher_term(self):
        election = elected()
        assert election.acquire("jm-b", now=31) == (
            "jm-b leads with term 2"
        )

    def test_renewal_holds_before_the_clock(self):
        election = elected()
        assert "renewed through" in election.renew("jm-a", now=10)

    def test_a_stranger_cannot_renew(self):
        with pytest.raises(Invalid):
            elected().renew("jm-b", now=5)


class TestTheFence:
    def test_current_term_assigns_freely(self):
        election = elected()
        assert election.assign("jm-a", 1, "p0") == (
            "p0 assigned under term 1"
        )

    def test_the_woken_zombie_is_refused_by_term(self):
        election = elected()
        election.assign("jm-a", 1, "p0")
        election.acquire("jm-b", now=31)
        election.assign("jm-b", 2, "p0")
        with pytest.raises(Halted) as caught:
            election.assign("jm-a", 1, "p1")
        assert "a stale term is a woken zombie" in str(
            caught.value
        )

    def test_the_summary_credits_the_term(self):
        election = elected()
        election.assign("jm-a", 1, "p0")
        election.acquire("jm-b", now=31)
        election.assign("jm-b", 2, "p0")
        with pytest.raises(Halted):
            election.assign("jm-a", 1, "p1")
        assert "the safety was the term, not the lease" in (
            election.incident_summary()
        )

    def test_a_quiet_election_has_no_incident(self):
        assert "either no split brain" in (
            elected().incident_summary()
        )
