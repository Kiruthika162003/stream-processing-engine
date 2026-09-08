from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.unionstream import UnionStream


def union() -> UnionStream:
    merged = UnionStream()
    merged.add_input("fast")
    merged.add_input("slow")
    return merged


class TestTheMinimumRule:
    def test_the_merged_watermark_is_the_slowest_input(self):
        merged = union()
        merged.advance("fast", 100)
        verdict = merged.advance("slow", 60)
        assert "merged watermark 60" in verdict
        assert "not the fastest" in verdict

    def test_input_watermarks_never_retreat(self):
        merged = union()
        merged.advance("fast", 100)
        with pytest.raises(Invalid):
            merged.advance("fast", 50)

    def test_a_stranger_input_is_refused(self):
        with pytest.raises(Invalid):
            union().advance("ghost", 5)


class TestIdleness:
    def test_an_idle_input_is_excused_from_the_minimum(self):
        merged = union()
        merged.advance("fast", 100)
        merged.advance("slow", 60)
        merged.mark_idle("slow")
        assert merged.merged_watermark() == 100

    def test_all_idle_leaves_no_opinion_about_time(self):
        merged = union()
        merged.advance("fast", 100)
        merged.mark_idle("fast")
        merged.mark_idle("slow")
        with pytest.raises(Invalid):
            merged.merged_watermark()

    def test_speaking_again_rejoins_the_minimum(self):
        merged = union()
        merged.advance("fast", 100)
        merged.advance("slow", 60)
        merged.mark_idle("slow")
        merged.advance("slow", 70)
        assert merged.merged_watermark() == 70


class TestTheNote:
    def test_the_note_explains_the_minimum(self):
        merged = union()
        merged.advance("fast", 100)
        note = merged.correctness_note()
        assert "2 input(s), 0 idle" in note
        assert "the slower input still holds" in note
