from __future__ import annotations

from examples import billingday


class TestBillingDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert billingday.main() == 0
        out = capsys.readouterr().out
        assert (
            "invariant holds: 2 order(s), every one with its "
            "row, 0 still owed"
        ) in out
        assert (
            "1 row(s), each exactly once, 1 replay(s) refused"
        ) in out
        assert (
            "acct-acme: 600 as of 30 event(s) ago"
        ) in out
        assert "exhausts on day 22" in out
        assert "policy overage" in out
