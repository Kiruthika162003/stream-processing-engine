"""Gale-Shapley: a matching where no two parties would both rather have each other.

Pairing two groups by mutual preference, workers to shifts,
consumers to partitions, requests to backends each with a
preference order, wants a matching that is stable: no unmatched
pair where both would prefer each other over whom they got, because
such a pair would defect and the assignment would not hold. Gale-
Shapley finds one by proposals. Each proposer approaches its
most-preferred receiver not yet rejected by; a receiver holding no
one tentatively accepts, and a receiver already holding someone
keeps whichever of the two it prefers and rejects the other, who
proposes on down its list. Rejected proposers keep proposing to
less-preferred receivers, receivers only ever trade up, and the
process ends when everyone is matched, with a matching provably
free of any blocking pair. The asymmetry worth knowing is that the
side doing the proposing gets its best possible stable partner and
the receiving side its worst, so who proposes matters even though
both orderings yield a stable result. This is the mechanism behind
residency matching and behind any assignment where both sides have
preferences and the pairing must not unravel. This module runs the
proposals and returns the matching, so its stability, the absence
of a pair that would both rather defect, is a checkable property.
"""

from __future__ import annotations

from collections import deque

from rill.errors import Invalid


def stable_matching(
    proposer_prefs: dict[str, list[str]], receiver_prefs: dict[str, list[str]]
) -> dict[str, str]:
    if len(proposer_prefs) != len(receiver_prefs):
        raise Invalid("the two sides must be the same size")
    rank = {
        receiver: {proposer: i for i, proposer in enumerate(order)}
        for receiver, order in receiver_prefs.items()
    }
    free = deque(proposer_prefs)
    next_choice = dict.fromkeys(proposer_prefs, 0)
    held: dict[str, str] = {}
    while free:
        proposer = free.popleft()
        order = proposer_prefs[proposer]
        if next_choice[proposer] >= len(order):
            continue
        receiver = order[next_choice[proposer]]
        next_choice[proposer] += 1
        if receiver not in rank:
            raise Invalid(f"unknown receiver {receiver}")
        current = held.get(receiver)
        if current is None:
            held[receiver] = proposer
        elif rank[receiver][proposer] < rank[receiver][current]:
            held[receiver] = proposer
            free.append(current)
        else:
            free.append(proposer)
    return {proposer: receiver for receiver, proposer in held.items()}
