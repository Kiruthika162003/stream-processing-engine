from __future__ import annotations

from rill.timerheap import TimerHeap


class TestFiring:
    def test_the_earliest_due_fires_first(self):
        heap = TimerHeap()
        heap.schedule("late", 100)
        heap.schedule("early", 50)
        assert heap.fire_due(60) == ["early"]

    def test_timers_past_the_watermark_all_fire(self):
        heap = TimerHeap()
        for number in range(5):
            heap.schedule(f"t-{number}", 10 + number)
        fired = heap.fire_due(100)
        assert len(fired) == 5


class TestLazyDeletion:
    def test_a_cancelled_timer_is_a_tombstone(self):
        heap = TimerHeap()
        heap.schedule("session-1", 100)
        verdict = heap.cancel("session-1")
        assert "every outstanding entry is a tombstone" in verdict
        assert heap.live_count == 0

    def test_a_cancelled_timer_never_fires(self):
        heap = TimerHeap()
        heap.schedule("session-1", 50)
        heap.cancel("session-1")
        assert heap.fire_due(100) == []

    def test_rescheduling_revives_a_cancelled_key(self):
        heap = TimerHeap()
        heap.schedule("session-1", 50)
        heap.cancel("session-1")
        heap.schedule("session-1", 60)
        assert heap.fire_due(100) == ["session-1"]


class TestCompaction:
    def test_a_mostly_tombstone_heap_wants_rebuilding(self):
        heap = TimerHeap()
        for number in range(10):
            heap.schedule(f"t-{number}", 100)
        for number in range(6):
            heap.cancel(f"t-{number}")
        note = heap.compaction_note()
        assert "tombstones: the heap spends its time skipping" in (
            note
        )

    def test_a_healthy_heap_needs_no_rebuild(self):
        heap = TimerHeap()
        for number in range(10):
            heap.schedule(f"t-{number}", 100)
        heap.cancel("t-0")
        assert "healthy, no rebuild needed" in (
            heap.compaction_note()
        )
