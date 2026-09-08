from __future__ import annotations

import pytest

from rill.errors import Invalid
from rill.tenantquota import TenantQuota


def quota(prefers_cutoff: bool = True) -> TenantQuota:
    return TenantQuota(
        tenant="acme",
        monthly_budget=1000,
        prefers_cutoff=prefers_cutoff,
    )


class TestTheWarnings:
    def test_the_half_warning_carries_the_exhaustion_date(self):
        chosen = quota()
        verdict = chosen.consume(510, day_of_month=10)
        assert verdict.startswith("acme at 50%")
        assert "exhausts on day 20" in verdict
        assert "a plan, not an escalation" in verdict

    def test_each_threshold_speaks_once(self):
        chosen = quota()
        chosen.consume(510, day_of_month=10)
        chosen.consume(300, day_of_month=15)
        chosen.consume(150, day_of_month=20)
        assert len(chosen.warnings) == 3

    def test_quiet_consumption_reports_its_share(self):
        chosen = quota()
        assert chosen.consume(100, day_of_month=3) == (
            "acme: 10% consumed"
        )


class TestTheTwoPolicies:
    def test_the_cutoff_tenant_is_refused_with_the_why(self):
        chosen = quota(prefers_cutoff=True)
        chosen.consume(1000, day_of_month=20)
        verdict = chosen.consume(50, day_of_month=21)
        assert verdict.startswith("acme REFUSED")
        assert "chose refusal over overage" in verdict

    def test_the_overage_tenant_is_billed_not_blocked(self):
        chosen = quota(prefers_cutoff=False)
        chosen.consume(1000, day_of_month=20)
        verdict = chosen.consume(50, day_of_month=21)
        assert "in overage by 50" in verdict
        assert "chose billing over refusal" in verdict

    def test_the_statement_records_the_choice(self):
        chosen = quota()
        chosen.consume(200, day_of_month=5)
        statement = chosen.statement()
        assert "policy cutoff" in statement
        assert "the invoice dispute will ask" in statement

    def test_budgetless_quotas_are_refused(self):
        with pytest.raises(Invalid):
            TenantQuota(
                tenant="x",
                monthly_budget=0,
                prefers_cutoff=True,
            )
