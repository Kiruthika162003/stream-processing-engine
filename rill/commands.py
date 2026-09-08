"""Commands and events: the request that may be refused, the fact that may not.

Event sourcing splits the write path into two words teams
conflate at their peril: a command is a request, withdraw
fifty, and the aggregate may refuse it; an event is a fact,
fifty was withdrawn, and nobody may refuse a fact, only
record it. The aggregate root holds the boundary: it replays
its events to know its state, validates each command against
that state, and either emits the event or returns the
refusal with its reason, and the refusal is an answer, not
an error, because insufficient-funds is a business outcome
the caller planned for. The tell is in the tenses, commands
imperative and events past, and the module enforces the
grammar mechanically, since the event named withdraw-money
is a command wearing a fact's clothes, and it will be
refused someday by code that has no right to refuse facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rill.errors import Invalid


@dataclass
class AccountAggregate:
    account_id: str
    events: list[tuple[str, int]] = field(default_factory=list)

    def balance(self) -> int:
        total = 0
        for name, amount in self.events:
            if name == "money-deposited":
                total += amount
            elif name == "money-withdrawn":
                total -= amount
        return total

    def handle(self, command: str, amount: int) -> str:
        if command.endswith("ed"):
            raise Invalid(
                f"{command} is past tense: a command is a "
                "request in the imperative, and an event "
                "named like a command will be refused someday "
                "by code with no right to refuse facts"
            )
        if amount <= 0:
            raise Invalid("amounts are positive")
        if command == "deposit":
            self.events.append(("money-deposited", amount))
            return f"money-deposited {amount}; a fact now"
        if command == "withdraw":
            if amount > self.balance():
                return (
                    f"REFUSED: withdraw {amount} against "
                    f"balance {self.balance()}; "
                    "insufficient-funds is an answer the "
                    "caller planned for, not an error"
                )
            self.events.append(("money-withdrawn", amount))
            return f"money-withdrawn {amount}; a fact now"
        raise Invalid(f"{command} is not a command this aggregate knows")

    def replay_check(self) -> str:
        replayed = AccountAggregate(
            account_id=self.account_id,
            events=list(self.events),
        )
        if replayed.balance() == self.balance():
            return (
                f"{len(self.events)} fact(s) replay to "
                f"balance {self.balance()}; the facts are the "
                "state"
            )
        return "DIVERGED: the replay disagrees with itself"
