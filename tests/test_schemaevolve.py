from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.schemaevolve import SchemaRegistry


def registry() -> SchemaRegistry:
    built = SchemaRegistry()
    built.publish(1, {"user": None, "amount": None})
    built.publish(
        2, {"user": None, "amount": None, "currency": 840}
    )
    return built


class TestTheMatrix:
    def test_old_reader_handles_new_writer(self):
        ok, why = registry().can_read(
            reader_version=1, writer_version=2
        )
        assert ok
        assert "handles" in why

    def test_new_reader_handles_old_writer_via_default(self):
        ok, _ = registry().can_read(
            reader_version=2, writer_version=1
        )
        assert ok

    def test_the_defaultless_addition_breaks_forward(self):
        built = registry()
        built.publish(
            3,
            {
                "user": None,
                "amount": None,
                "currency": 840,
                "region": None,
            },
        )
        ok, why = built.can_read(
            reader_version=3, writer_version=1
        )
        assert not ok
        assert "no default to fall back on" in why

    def test_the_full_matrix_names_the_classic_outage(self):
        built = registry()
        built.publish(
            3,
            {
                "user": None,
                "amount": None,
                "currency": 840,
                "region": None,
            },
        )
        matrix = built.deploy_matrix()
        assert "2 broken pair(s)" in matrix
        assert "another team's schedule" in matrix

    def test_a_clean_pair_of_versions_deploys_any_order(self):
        assert "every pair reads; deploy in any order" in (
            registry().deploy_matrix()
        )


class TestRemovalLaw:
    def test_removing_a_required_field_is_refused(self):
        built = registry()
        with pytest.raises(Invalid) as caught:
            built.publish(3, {"user": None, "currency": 840})
        assert "two releases by law" in str(caught.value)

    def test_the_two_release_path_is_legal(self):
        built = registry()
        built.publish(
            3, {"user": None, "amount": 0, "currency": 840}
        )
        verdict = built.publish(
            4, {"user": None, "currency": 840}
        )
        assert verdict == "schema v4 published"

    def test_versions_publish_in_order(self):
        with pytest.raises(Invalid):
            registry().publish(9, {"a": None})
