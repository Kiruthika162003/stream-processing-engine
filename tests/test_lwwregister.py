from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.lwwregister import LWWRegister


class TestWrite:
    def test_a_newer_write_replaces_an_older_one(self):
        reg = LWWRegister("a")
        reg.write("first", stamp=1)
        reg.write("second", stamp=2)
        assert reg.value() == "second"

    def test_an_older_write_is_ignored(self):
        reg = LWWRegister("a")
        reg.write("second", stamp=2)
        reg.write("stale", stamp=1)
        assert reg.value() == "second"


class TestConcurrentResolution:
    def test_a_same_stamp_clash_resolves_by_node_id(self):
        alice = LWWRegister("a")
        alice.write("alice", stamp=5)
        bob = LWWRegister("b")
        bob.write("bob", stamp=5)
        alice.merge(bob)
        bob.merge(alice)
        # b > a, so both converge on bob's write deterministically
        assert alice.value() == "bob"
        assert bob.value() == "bob"

    def test_the_merge_names_the_discarded_write(self):
        alice = LWWRegister("a")
        alice.write("alice", stamp=5)
        bob = LWWRegister("b")
        bob.write("bob", stamp=5)
        assert alice.merge(bob) == "alice"

    def test_replicas_converge_regardless_of_direction(self):
        alice = LWWRegister("a")
        alice.write("x", stamp=3)
        bob = LWWRegister("b")
        bob.write("y", stamp=7)
        alice.merge(bob)
        bob.merge(alice)
        assert alice.value() == bob.value() == "y"


class TestRefusals:
    def test_a_negative_stamp_is_refused(self):
        with pytest.raises(Invalid):
            LWWRegister("a").write("v", stamp=-1)
