"""Max-min fairness: an equal split, except the small demands hand back what they cannot use.

Dividing a fixed capacity among competing demands fairly is not
an equal split, because an equal split wastes the share it hands
to a demand that wanted less. Max-min fairness does the right
thing: it maximizes the smallest allocation, which works out to
giving every demand an equal share of the capacity, except that a
demand asking for less than its share takes only what it needs and
returns the rest, and that freed capacity is redistributed as an
equal share among the demands still wanting more, repeated until
nothing is left over or every demand is satisfied. So a small
demand is fully met while the large demands split what remains,
and no demand can be raised without lowering another that was
already smaller, which is the formal fairness the name promises.
This matters wherever a shared resource meets uneven appetites,
link bandwidth across flows, worker slots across tenants, and the
naive equal division either starves the large demands or wastes
capacity on the small ones. This module computes the allocation
and its redistribution, so the fair share, and the way a modest
demand's leftover flows to the hungrier ones, are a measured
vector rather than a definition.
"""

from __future__ import annotations

from rill.errors import Invalid


def max_min_fair(demands: list[int], capacity: int) -> list[int]:
    if not demands:
        raise Invalid("no demands")
    if capacity < 0:
        raise Invalid("capacity cannot be negative")
    if any(demand < 0 for demand in demands):
        raise Invalid("demands cannot be negative")
    allocations = [0] * len(demands)
    remaining = capacity
    unsatisfied = {i for i, demand in enumerate(demands) if demand > 0}
    while unsatisfied and remaining > 0:
        share = remaining // len(unsatisfied)
        if share == 0:
            for index in sorted(unsatisfied):
                if remaining == 0:
                    break
                allocations[index] += 1
                remaining -= 1
            break
        for index in sorted(unsatisfied):
            give = min(share, demands[index] - allocations[index])
            allocations[index] += give
            remaining -= give
            if allocations[index] == demands[index]:
                unsatisfied.discard(index)
    return allocations
