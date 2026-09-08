from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.trie import Trie


def _built() -> Trie:
    trie = Trie()
    for word in ("car", "card", "care", "cat", "dog"):
        trie.add(word)
    return trie


class TestMembership:
    def test_added_words_are_present(self):
        trie = _built()
        assert trie.contains("car")
        assert trie.contains("card")

    def test_a_prefix_is_not_a_member_unless_added(self):
        trie = Trie()
        trie.add("card")
        assert not trie.contains("car")

    def test_an_absent_word_is_not_present(self):
        assert not _built().contains("cow")


class TestPrefix:
    def test_prefix_returns_only_the_completions(self):
        trie = _built()
        assert trie.with_prefix("car") == ["car", "card", "care"]

    def test_a_prefix_matching_nothing_returns_empty(self):
        assert _built().with_prefix("z") == []

    def test_the_whole_dictionary_is_reachable_from_the_empty_prefix(self):
        assert _built().with_prefix("") == ["car", "card", "care", "cat", "dog"]


class TestRefusals:
    def test_adding_an_empty_string_is_refused(self):
        with pytest.raises(Invalid):
            Trie().add("")
