from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.schemaregistry import Schema, SchemaRegistry, classify

BASE = Schema(
    version=1,
    required=frozenset({"id", "amount"}),
    optional=frozenset({"note"}),
)


class TestClassification:
    def test_an_optional_field_is_full_compatibility(self):
        evolved = Schema(
            version=2,
            required=BASE.required,
            optional=BASE.optional | {"tag"},
        )
        assert classify(BASE, evolved) == "full"

    def test_removing_a_field_keeps_backward_only(self):
        evolved = Schema(
            version=2,
            required=frozenset({"id"}),
            optional=BASE.optional,
        )
        assert classify(BASE, evolved) == "backward-only"

    def test_adding_a_required_field_keeps_forward_only(self):
        evolved = Schema(
            version=2,
            required=BASE.required | {"currency"},
            optional=BASE.optional,
        )
        assert classify(BASE, evolved) == "forward-only"

    def test_a_rename_breaks_both(self):
        evolved = Schema(
            version=2,
            required=frozenset({"id", "total"}),
            optional=BASE.optional,
        )
        assert classify(BASE, evolved) == "none"


class TestTheGate:
    def test_full_compatibility_needs_no_window(self):
        registry = SchemaRegistry(current=BASE)
        evolved = Schema(
            version=2,
            required=BASE.required,
            optional=BASE.optional | {"tag"},
        )
        assert "safe under any deploy order" in registry.propose(
            evolved
        )

    def test_a_breaking_change_demands_a_migration_window(self):
        registry = SchemaRegistry(current=BASE)
        evolved = Schema(
            version=2,
            required=BASE.required | {"currency"},
            optional=BASE.optional,
        )
        with pytest.raises(Invalid) as caught:
            registry.propose(evolved)
        assert "fleets are never atomic" in str(caught.value)

    def test_the_window_lets_the_breaking_change_land(self):
        registry = SchemaRegistry(current=BASE)
        evolved = Schema(
            version=2,
            required=BASE.required | {"currency"},
            optional=BASE.optional,
        )
        verdict = registry.propose(evolved, migration_window=100)
        assert "100-window migration" in verdict
        assert registry.migration_windows[2] == 100
