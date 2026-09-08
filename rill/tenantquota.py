"""Tenant quotas: the monthly budget, the burst that borrows, the cutoff that warns.

Rate limits police the second; quotas police the month, and
the difference is social: a tenant over its per-second rate
is throttled and retries, while a tenant out of monthly
quota is a customer conversation, so the machinery must
produce warnings long before refusals. The ledger tracks
consumption against the period's budget and speaks at the
thresholds that give the conversation time, half, eighty,
and ninety-five percent, each with the projected exhaustion
date computed from the tenant's own run rate, because "you
will run out on the 23rd at this pace" starts a plan and
"quota exceeded" starts an escalation. The hard cutoff is
configurable per tenant precisely because some tenants
prefer refusal to overage billing and some the reverse, and
the ledger records which they chose, since the invoice
dispute will ask.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid

THRESHOLDS = (50, 80, 95)


@dataclass
class TenantQuota:
    tenant: str
    monthly_budget: int
    prefers_cutoff: bool
    consumed: int = 0
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.monthly_budget < 1:
            raise Invalid("a quota needs a budget")

    def consume(
        self, count: int, day_of_month: int
    ) -> str:
        if count < 1 or not 1 <= day_of_month <= 31:
            raise Invalid("positive counts, real days")
        before_share = 100 * self.consumed // self.monthly_budget
        if (
            self.consumed >= self.monthly_budget
            and self.prefers_cutoff
        ):
            return (
                f"{self.tenant} REFUSED: quota exhausted and "
                "this tenant chose refusal over overage, "
                "which the invoice dispute will ask about"
            )
        self.consumed += count
        after_share = 100 * self.consumed // self.monthly_budget
        for threshold in THRESHOLDS:
            if before_share < threshold <= after_share:
                run_rate = self.consumed / day_of_month
                exhaustion_day = (
                    self.monthly_budget / run_rate
                )
                warning = (
                    f"{self.tenant} at {threshold}%: at this "
                    f"pace the budget exhausts on day "
                    f"{exhaustion_day:.0f}; a plan, not an "
                    "escalation"
                )
                self.warnings.append(warning)
                return warning
        if self.consumed > self.monthly_budget:
            overage = self.consumed - self.monthly_budget
            return (
                f"{self.tenant} in overage by {overage}; this "
                "tenant chose billing over refusal"
            )
        return f"{self.tenant}: {after_share}% consumed"

    def statement(self) -> str:
        choice = (
            "cutoff" if self.prefers_cutoff else "overage"
        )
        return (
            f"{self.tenant}: {self.consumed} of "
            f"{self.monthly_budget}, "
            f"{len(self.warnings)} warning(s) issued, policy "
            f"{choice}; recorded, since the invoice dispute "
            "will ask"
        )
