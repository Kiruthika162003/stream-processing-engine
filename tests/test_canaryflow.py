from __future__ import annotations

import pytest

from rill.canaryflow import CanaryRouter
from rill.errors import Invalid

KEYS = [f"key-{number}" for number in range(200)]


def router() -> CanaryRouter:
    return CanaryRouter(canary_percent=20)


class TestTheSlice:
    def test_the_slice_is_deterministic(self):
        first = router()
        second = router()
        for key in KEYS:
            assert first.routes_to_canary(
                key
            ) == second.routes_to_canary(key)

    def test_the_new_operator_refuses_out_of_slice_keys(self):
        chosen = router()
        outsider = next(
            key for key in KEYS if not chosen.routes_to_canary(key)
        )
        with pytest.raises(Invalid) as caught:
            chosen.record_new(outsider, 5)
        assert "splits its state" in str(caught.value)

    def test_a_whole_flock_canary_is_refused(self):
        with pytest.raises(Invalid):
            CanaryRouter(canary_percent=80)


class TestTheGate:
    def test_a_tiny_slice_is_held(self):
        chosen = router()
        canary = [
            key for key in KEYS if chosen.routes_to_canary(key)
        ][:5]
        for key in canary:
            chosen.record_old(key, 1)
            chosen.record_new(key, 1)
        assert "too small a slice to trust" in (
            chosen.promotion_gate()
        )

    def test_agreement_promotes(self):
        chosen = router()
        canary = [
            key for key in KEYS if chosen.routes_to_canary(key)
        ]
        for key in canary:
            chosen.record_old(key, 7)
            chosen.record_new(key, 7)
        verdict = chosen.promotion_gate()
        assert verdict.startswith("PROMOTE: 34 keys compared")

    def test_disagreement_names_the_keys(self):
        chosen = router()
        canary = [
            key for key in KEYS if chosen.routes_to_canary(key)
        ]
        for index, key in enumerate(canary):
            chosen.record_old(key, 7)
            chosen.record_new(key, 7 if index >= 5 else 99)
        verdict = chosen.promotion_gate()
        assert verdict.startswith("HOLD: agreement")
        assert "the fix lives in each key's history" in verdict
