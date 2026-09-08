from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.idletimeout import IdleCoordinator


class TestPinnedWithoutEjection:
    def test_a_quiet_source_pins_the_minimum_before_the_timeout(self):
        coord = IdleCoordinator(idle_timeout=100)
        coord.observe("fast", watermark=50, now=0)
        coord.observe("slow", watermark=10, now=0)
        coord.observe("fast", watermark=500, now=90)
        assert coord.combined(now=90) == 10


class TestEjection:
    def test_the_timeout_evicts_the_idle_source_and_frees_the_watermark(self):
        coord = IdleCoordinator(idle_timeout=100)
        coord.observe("fast", watermark=50, now=0)
        coord.observe("slow", watermark=10, now=0)
        coord.observe("fast", watermark=500, now=200)
        assert coord.idle_sources(now=200) == ["slow"]
        assert coord.combined(now=200) == 500

    def test_all_idle_leaves_no_combined_watermark(self):
        coord = IdleCoordinator(idle_timeout=100)
        coord.observe("a", watermark=10, now=0)
        with pytest.raises(Invalid):
            coord.combined(now=200)


class TestReturnIsLate:
    def test_a_returning_source_is_late_by_the_climb_it_missed(self):
        coord = IdleCoordinator(idle_timeout=100)
        coord.observe("fast", watermark=50, now=0)
        coord.observe("slow", watermark=10, now=0)
        coord.observe("fast", watermark=500, now=200)
        assert coord.lateness_on_return("slow", now=200) == 490

    def test_a_source_at_the_front_returns_without_lateness(self):
        coord = IdleCoordinator(idle_timeout=100)
        coord.observe("a", watermark=50, now=0)
        coord.observe("b", watermark=50, now=0)
        assert coord.lateness_on_return("a", now=0) == 0


class TestRefusals:
    def test_a_nonpositive_timeout_is_refused(self):
        with pytest.raises(Invalid):
            IdleCoordinator(idle_timeout=0)

    def test_a_backward_watermark_is_refused(self):
        coord = IdleCoordinator(idle_timeout=100)
        coord.observe("a", watermark=50, now=0)
        with pytest.raises(Invalid):
            coord.observe("a", watermark=10, now=1)
