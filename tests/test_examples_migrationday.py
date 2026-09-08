from __future__ import annotations

from examples import migrationday


class TestMigrationDay:
    def test_the_day_reads_end_to_end(self, capsys):
        assert migrationday.main() == 0
        out = capsys.readouterr().out
        assert (
            "v2 accepted with a 100-window migration: "
            "forward-only compatibility"
        ) in out
        assert "migrated v1 -> v3 through 2 step(s)" in out
        assert "modulo: 384 of 500 key(s) move (76%)" in out
        assert "sticky-groups: 106 of 500 key(s) move (21%)" in out
        assert (
            "rescaled to 8: 112 key group(s) reassigned whole"
        ) in out
        assert "accelerated 1000 (31000x)" in out
