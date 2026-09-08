from __future__ import annotations

import pytest

from rill.emitpolicy import EmitPolicy
from rill.errors import Invalid


class TestOnChange:
    def test_it_emits_on_every_move(self):
        policy = EmitPolicy(policy="on-change")
        assert policy.update(5, now=1) is not None
        assert policy.update(5, now=2) is None
        assert policy.update(6, now=3) is not None

    def test_the_note_warns_the_averaging_consumer(self):
        note = EmitPolicy(policy="on-change").downstream_note()
        assert "gets garbage from this" in note


class TestOnInterval:
    def test_the_heartbeat_fires_regardless(self):
        policy = EmitPolicy(policy="on-interval", interval=10)
        assert policy.update(5, now=0) is not None
        assert policy.update(5, now=5) is None
        assert policy.update(5, now=10) is not None

    def test_a_missing_interval_is_refused(self):
        with pytest.raises(Invalid):
            EmitPolicy(policy="on-interval", interval=0)


class TestOnThreshold:
    def test_only_crossings_emit(self):
        policy = EmitPolicy(policy="on-threshold", threshold=100)
        assert policy.update(50, now=1) is None
        assert policy.update(150, now=2) is not None
        assert policy.update(160, now=3) is None
        assert policy.update(80, now=4) is not None

    def test_a_missing_threshold_is_refused(self):
        with pytest.raises(Invalid):
            EmitPolicy(policy="on-threshold", threshold=0)


class TestTheDeclaration:
    def test_the_whim_policy_is_refused(self):
        with pytest.raises(Invalid) as caught:
            EmitPolicy(policy="whenever")
        assert "downstream nobody can reason about" in str(
            caught.value
        )

    def test_every_policy_has_a_downstream_note(self):
        for name, extra in (
            ("on-change", {}),
            ("on-interval", {"interval": 5}),
            ("on-threshold", {"threshold": 5}),
        ):
            note = EmitPolicy(policy=name, **extra).downstream_note()
            assert name in note
