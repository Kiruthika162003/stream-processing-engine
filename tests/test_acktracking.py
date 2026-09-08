from __future__ import annotations

import pytest

from rill.acktracking import AckTracker
from rill.errors import Invalid


class TestTheAckTree:
    def test_a_root_is_done_when_its_children_ack(self):
        tracker = AckTracker()
        tracker.emit_root("root-1", children=2, now=0)
        tracker.ack("root-1", new_children=0, now=1)
        verdict = tracker.ack("root-1", new_children=0, now=2)
        assert "fully acked" in verdict
        assert "advance its offset" in verdict

    def test_a_child_that_spawns_keeps_the_root_pending(self):
        tracker = AckTracker()
        tracker.emit_root("root-1", children=1, now=0)
        verdict = tracker.ack("root-1", new_children=3, now=1)
        assert "3 still pending" in verdict

    def test_a_childless_root_is_refused(self):
        with pytest.raises(Invalid):
            AckTracker().emit_root("root-1", children=0, now=0)

    def test_acking_an_unknown_root_is_refused(self):
        with pytest.raises(Invalid):
            AckTracker().ack("ghost", new_children=0, now=1)


class TestTimeouts:
    def test_a_stalled_tree_is_replayed_and_named(self):
        tracker = AckTracker()
        tracker.emit_root("root-1", children=2, now=0)
        verdict = tracker.sweep_timeouts(now=100, deadline=50)
        assert "root-1 (stalled)" in verdict
        assert "at-least-once guarantee in action" in verdict

    def test_a_slow_but_progressing_tree_is_named_slow(self):
        tracker = AckTracker()
        tracker.emit_root("root-1", children=2, now=0)
        tracker.ack("root-1", new_children=0, now=90)
        verdict = tracker.sweep_timeouts(now=100, deadline=50)
        assert "root-1 (slow)" in verdict

    def test_progressing_trees_are_left_alone(self):
        tracker = AckTracker()
        tracker.emit_root("root-1", children=2, now=0)
        assert "every tree progressing" in tracker.sweep_timeouts(
            now=10, deadline=50
        )
