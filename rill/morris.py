"""Morris counter: counting to a billion in a byte by storing the exponent, not the count.

Counting events exactly needs enough bits to hold the count, and
for a stream of billions across millions of counters that is real
memory. The Morris counter spends log-log of the count instead by
storing not the count but its exponent. It holds a small number n
and treats the estimate as two to the n minus one, and on each
increment it bumps n only with probability one over two-to-the-n,
so early increments almost always raise n and later ones almost
never do, keeping n near the logarithm of the true count. A single
counter is noisy, since n is a random variable and two-to-the-n is
a coarse ladder, but the estimate is unbiased: averaged over many
counters or many runs it converges to the true count, which is
what makes a fleet of Morris counters accurate in aggregate even
though any one is rough. The trade is exactness for a logarithmic
shrink in the state, right when there are far more counters than
bits to spend and an approximate count is enough. This module
keeps the exponent, increments it probabilistically from an
injected random source, and reports the estimate, so the
unbiasedness and the log-sized state are measured rather than
asserted.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from rill.errors import Invalid


@dataclass
class MorrisCounter:
    _exponent: int = 0

    def increment(self, uniform: Callable[[], float]) -> None:
        roll = uniform()
        if not 0.0 <= roll < 1.0:
            raise Invalid("uniform must return a value in [0, 1)")
        if roll < 2.0 ** (-self._exponent):
            self._exponent += 1

    def estimate(self) -> int:
        return 2**self._exponent - 1

    def exponent(self) -> int:
        return self._exponent
