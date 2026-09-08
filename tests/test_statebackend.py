from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.statebackend import StateProfile


class TestSizing:
    def test_a_small_state_fits_in_memory(self):
        profile = StateProfile(
            key_cardinality=1000,
            bytes_per_key=100,
            memory_budget_bytes=1_000_000,
        )
        assert profile.fits_in_memory()

    def test_a_large_state_overflows_memory(self):
        profile = StateProfile(
            key_cardinality=1_000_000,
            bytes_per_key=1000,
            memory_budget_bytes=1_000_000,
        )
        assert not profile.fits_in_memory()

    def test_degenerate_profiles_are_refused(self):
        with pytest.raises(Invalid):
            StateProfile(
                key_cardinality=0,
                bytes_per_key=1,
                memory_budget_bytes=1,
            )


class TestRecommendation:
    def test_the_fitting_state_gets_the_memory_backend(self):
        profile = StateProfile(
            key_cardinality=1000,
            bytes_per_key=100,
            memory_budget_bytes=1_000_000,
        )
        rec = profile.recommend()
        assert "memory backend" in rec
        assert "fastest access" in rec

    def test_the_overflow_demands_disk_with_the_reason(self):
        profile = StateProfile(
            key_cardinality=1_000_000,
            bytes_per_key=1000,
            memory_budget_bytes=1_000_000,
        )
        rec = profile.recommend()
        assert "disk backend required" in rec
        assert "not slowly but fatally" in rec

    def test_the_access_note_prices_the_latency(self):
        profile = StateProfile(
            key_cardinality=1_000_000,
            bytes_per_key=1000,
            memory_budget_bytes=1_000_000,
        )
        note = profile.access_cost_note()
        assert "100x latency" in note
        assert "not optional at this state size" in note
