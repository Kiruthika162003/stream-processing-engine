from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.exactlyoncefile import FileCommitter


class TestTheCommitProtocol:
    def test_a_staged_file_is_not_yet_visible(self):
        committer = FileCommitter()
        verdict = committer.stage("part-001.json", "data")
        assert "not yet visible" in verdict
        assert "part-001.json" not in committer.finalized

    def test_the_checkpoint_finalizes_staged_files(self):
        committer = FileCommitter()
        committer.stage("part-001.json", "data")
        verdict = committer.commit_checkpoint(["part-001.json"])
        assert "1 file(s) renamed to final" in verdict
        assert "part-001.json" in committer.finalized

    def test_finalizing_unstaged_is_refused(self):
        committer = FileCommitter()
        with pytest.raises(Invalid) as caught:
            committer.commit_checkpoint(["ghost.json"])
        assert "no content behind it" in str(caught.value)

    def test_finalizing_before_the_checkpoint_is_refused(self):
        committer = FileCommitter()
        committer.stage("part-001.json", "data")
        with pytest.raises(Invalid) as caught:
            committer.finalize_before_checkpoint("part-001.json")
        assert "the file system's back door" in str(caught.value)


class TestRecovery:
    def test_recovery_cleans_orphans_and_keeps_finalized(self):
        committer = FileCommitter()
        committer.stage("done.json", "d")
        committer.commit_checkpoint(["done.json"])
        committer.stage("orphan.json", "d")
        verdict = committer.recover()
        assert "cleaned 1 orphan temp file(s)" in verdict
        assert "kept 1 finalized" in verdict
        assert committer.orphans_cleaned == 1
