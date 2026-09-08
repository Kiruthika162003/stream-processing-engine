"""Coin change: the take-the-largest greedy that is optimal for some coin systems, not all.

Making an amount with the fewest coins from a set of
denominations has a greedy everyone reaches for, take the largest
coin that fits and repeat, and it is optimal, for the coin systems
it happens to be optimal for. Real currencies are usually designed
to be canonical, meaning the greedy works, which is why it feels
like a law rather than a coincidence. It is a coincidence. Give
the greedy a non-canonical set, coins of one, three, and four,
and ask for six, and it takes a four then two ones for three
coins, missing the two threes that make six in two. The greedy's
mistake is committing to the largest coin without seeing that a
slightly smaller one composes better with what remains, the same
local-commitment error that sinks greedy on the zero-one
knapsack. The general answer is dynamic programming: the fewest
coins for an amount is one plus the fewest for the amount minus
some coin, minimized over the coins, built up from zero. It is
optimal for every coin system, canonical or not, at the cost of a
table the size of the amount. This module runs the DP and the
largest-first greedy side by side, so the extra coins the greedy
spends on a non-canonical system are a measured difference rather
than a surprise at the register.
"""

from __future__ import annotations

from rill.errors import Invalid

IMPOSSIBLE = -1


def min_coins(coins: list[int], amount: int) -> int:
    if amount < 0:
        raise Invalid("amount cannot be negative")
    if any(coin <= 0 for coin in coins):
        raise Invalid("coins must be positive")
    best = [0] + [amount + 1] * amount
    for target in range(1, amount + 1):
        for coin in coins:
            if coin <= target:
                best[target] = min(best[target], best[target - coin] + 1)
    return best[amount] if best[amount] <= amount else IMPOSSIBLE


def greedy_coins(coins: list[int], amount: int) -> int:
    remaining = amount
    used = 0
    for coin in sorted(coins, reverse=True):
        while coin <= remaining:
            remaining -= coin
            used += 1
    return used if remaining == 0 else IMPOSSIBLE
