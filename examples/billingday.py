"""A billing day: the outbox, the epochs, the view, and the invoice's defense.

Run with: python -m examples.billingday
"""

from __future__ import annotations

from rill.epochs import EpochSink
from rill.outbox import OutboxService
from rill.readmodel import ReadModel
from rill.tenantquota import TenantQuota


def morning_the_orders():
    service = OutboxService()
    service.place_order("ord-1", 500)
    service.place_order("ord-2", 300)
    service.relay_once(crash_before_mark=True)
    service.relay_once()
    service.relay_once()
    print(f"orders:  {service.invariant_audit()}")


def midday_the_ledger():
    sink = EpochSink()
    sink.stage(1, "invoice-1")
    sink.commit(1)
    sink.crash_recovery()
    sink.commit(1)
    print(f"ledger:  {sink.audit()}")


def afternoon_the_balance():
    model = ReadModel()
    for position, delta in enumerate((500, 300, -200)):
        model.apply(position, "acct-acme", delta)
    print(f"balance: {model.query('acct-acme', stream_head=33)}")


def evening_the_quota():
    quota = TenantQuota(
        tenant="acme", monthly_budget=1000, prefers_cutoff=False
    )
    quota.consume(810, day_of_month=18)
    print(f"quota:   {quota.warnings[-1]}")
    print(f"         {quota.statement()}")


def main() -> int:
    morning_the_orders()
    midday_the_ledger()
    afternoon_the_balance()
    evening_the_quota()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
