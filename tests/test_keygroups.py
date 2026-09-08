from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.keygroups import KeyGroupAssignment


def job() -> KeyGroupAssignment:
    return KeyGroupAssignment(key_groups=128, parallelism=4)


class TestAssignment:
    def test_every_key_group_has_exactly_one_owner(self):
        assignment = job()
        owners = {
            assignment.owner_of(group) for group in range(128)
        }
        assert owners == {0, 1, 2, 3}

    def test_parallelism_cannot_exceed_the_key_groups(self):
        with pytest.raises(Invalid) as caught:
            KeyGroupAssignment(key_groups=4, parallelism=8)
        assert "the ceiling found on growth day" in str(
            caught.value
        )

    def test_an_out_of_range_group_is_refused(self):
        with pytest.raises(Invalid):
            job().owner_of(200)


class TestRescaling:
    def test_scaling_up_reassigns_whole_key_groups(self):
        assignment = job()
        verdict = assignment.rescale(new_parallelism=8)
        assert "rescaled to 8" in verdict
        assert "no key split, state followed its group" in verdict
        assert assignment.parallelism == 8

    def test_scaling_past_the_ceiling_is_refused(self):
        assignment = job()
        with pytest.raises(Invalid) as caught:
            assignment.rescale(new_parallelism=256)
        assert "set once at creation and never raised" in str(
            caught.value
        )

    def test_scaling_to_zero_is_refused(self):
        with pytest.raises(Invalid):
            job().rescale(new_parallelism=0)

    def test_every_group_still_owned_after_rescale(self):
        assignment = job()
        assignment.rescale(new_parallelism=16)
        owners = {
            assignment.owner_of(group) for group in range(128)
        }
        assert owners == set(range(16))
