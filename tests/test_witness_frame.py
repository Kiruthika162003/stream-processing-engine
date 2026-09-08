from __future__ import annotations

import pytest

from rill.cli import main
from rill.errors import Invalid
from rill.witnesses.deposition import Deposition
from rill.witnesses.registry import all_depositions, report


class TestDeposition:
    def test_deposition_reads_as_a_checkable_sentence(self):
        told = Deposition(
            witness="boundbet",
            claim="the bound is a bet and here is the bill",
            numbers={"late": 3},
            holds=True,
        )
        assert told.line() == (
            "[HOLDS] boundbet: the bound is a bet and here is "
            "the bill"
        )
        assert "late = 3" in told.detail()

    def test_anonymous_assertions_are_rumors(self):
        with pytest.raises(Invalid):
            Deposition(witness=" ", claim="something")

    def test_a_broken_deposition_says_so_first(self):
        told = Deposition(
            witness="w", claim="c", holds=False
        )
        assert told.line().startswith("[BROKEN]")


class TestTheRegistry:
    def test_the_registry_counts_its_own_roster(self):
        depositions = all_depositions()
        assert report().endswith(
            f"{len(depositions)} witnesses, 0 broken"
        )
        assert all(d.holds for d in depositions)


class TestTheCli:
    def test_summary_prints_the_one_line(self, capsys):
        assert main(["summary"]) == 0
        out = capsys.readouterr().out.strip()
        assert out == (
            f"{len(all_depositions())} witnesses (0 broken)"
        )

    def test_check_holds_on_an_empty_registry(self, capsys):
        assert main(["check"]) == 0
        assert "all witnesses hold" in capsys.readouterr().out

    def test_no_command_prints_help(self, capsys):
        assert main([]) == 2
        assert "witnesses" in capsys.readouterr().out
