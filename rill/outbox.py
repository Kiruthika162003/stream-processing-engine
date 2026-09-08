"""The transactional outbox: the database and the stream stop lying to each other.

A service that writes its database and then publishes an
event performs two commits with no transaction across them,
and the failure between the two is the dual-write bug: the
order exists but its event never happened, or the event went
out for an order that rolled back. The outbox closes the gap
by refusing the second commit: the event is written into the
same database transaction as the state change, into an outbox
table, and a relay reads the outbox and publishes, so the
event exists if and only if the write committed. The relay is
at-least-once by nature, crash between publish and
mark-published duplicates the event, which is why outbox rows
carry identities for the downstream deduper, and the audit
here is the invariant the pattern exists for: no event
without its row, no committed row without its event,
eventually, and eventually is measured, not waved at.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class OutboxService:
    orders: dict[str, int] = field(default_factory=dict)
    outbox: list[tuple[str, str, bool]] = field(
        default_factory=list
    )
    published: list[str] = field(default_factory=list)

    def place_order(
        self, order_id: str, amount: int, crash_mid_write: bool = False
    ) -> str:
        if not order_id:
            raise Invalid("orders carry identities")
        if crash_mid_write:
            return (
                f"{order_id}: transaction rolled back; no "
                "order, no outbox row, no event, no lie"
            )
        self.orders[order_id] = amount
        self.outbox.append((order_id, f"placed:{amount}", False))
        return (
            f"{order_id}: state and event committed together; "
            "the event exists iff the write did"
        )

    def relay_once(self, crash_before_mark: bool = False) -> str:
        pending = [
            (index, row)
            for index, row in enumerate(self.outbox)
            if not row[2]
        ]
        if not pending:
            return "outbox drained; nothing owed"
        index, (order_id, payload, _) = pending[0]
        self.published.append(f"{order_id}|{payload}")
        if crash_before_mark:
            return (
                f"{order_id} published then crashed before the "
                "mark; the relay will publish it again, which "
                "is why outbox rows carry identities for the "
                "deduper"
            )
        self.outbox[index] = (order_id, payload, True)
        return f"{order_id} published and marked"

    def invariant_audit(self) -> str:
        rows = {order_id for order_id, _, _ in self.outbox}
        missing_rows = sorted(set(self.orders) - rows)
        if missing_rows:
            return (
                f"DUAL-WRITE: {', '.join(missing_rows)} exist "
                "without outbox rows; the pattern was bypassed"
            )
        unpublished = [
            order_id
            for order_id, _, marked in self.outbox
            if not marked
        ]
        published_ids = {
            line.split("|")[0] for line in self.published
        }
        ghost_events = sorted(published_ids - set(self.orders))
        if ghost_events:
            return (
                f"GHOST: event(s) for {', '.join(ghost_events)} "
                "without committed orders"
            )
        return (
            f"invariant holds: {len(self.orders)} order(s), "
            f"every one with its row, {len(unpublished)} "
            "still owed to the stream; eventually, measured"
        )
