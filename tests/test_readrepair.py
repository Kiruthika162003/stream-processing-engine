from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.readrepair import diverged, read_repair


class TestAgreement:
    def test_replicas_that_agree_need_no_repair(self):
        answers = {"a": ("v2", 2), "b": ("v2", 2), "c": ("v2", 2)}
        result = read_repair(answers)
        assert result.value == "v2"
        assert result.repairs == ()
        assert not diverged(answers)


class TestRepair:
    def test_the_newest_version_wins_and_the_stale_is_repaired(self):
        answers = {"a": ("new", 5), "b": ("old", 3)}
        result = read_repair(answers)
        assert result.value == "new"
        assert result.version == 5
        assert result.repairs == ("b",)
        assert diverged(answers)

    def test_every_older_replica_is_listed_for_repair(self):
        answers = {
            "a": ("new", 5),
            "b": ("old", 3),
            "c": ("older", 1),
            "d": ("new", 5),
        }
        result = read_repair(answers)
        assert result.repairs == ("b", "c")


class TestRefusals:
    def test_no_answers_is_refused(self):
        with pytest.raises(Invalid):
            read_repair({})
