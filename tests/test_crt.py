from __future__ import annotations

import math
import random

import pytest

from rill.crt import crt
from rill.errors import Invalid


class TestSolve:
    def test_the_classic_soldiers_problem(self):
        assert crt([3, 2], [5, 7]) == (23, 35)

    def test_a_single_congruence_returns_itself(self):
        assert crt([4], [9]) == (4, 9)

    def test_it_satisfies_every_congruence_and_matches_brute(self):
        def coprime_set(rng):
            mods: list[int] = []
            while len(mods) < rng.randint(2, 4):
                c = rng.randint(2, 20)
                if all(math.gcd(c, m) == 1 for m in mods):
                    mods.append(c)
            return mods

        rng = random.Random(37)
        for _ in range(3000):
            mods = coprime_set(rng)
            target = rng.randint(0, 10**6)
            rems = [target % m for m in mods]
            x, modulus = crt(rems, mods)
            assert modulus == math.prod(mods)
            assert all(x % m == r for r, m in zip(rems, mods, strict=True))
            brute = next(
                v for v in range(modulus)
                if all(v % m == r for r, m in zip(rems, mods, strict=True))
            )
            assert x == brute


class TestRefusals:
    def test_contradictory_non_coprime_moduli_are_refused(self):
        # x == 0 (mod 2) and x == 1 (mod 4) cannot both hold
        with pytest.raises(Invalid):
            crt([0, 1], [2, 4])

    def test_mismatched_lengths_are_refused(self):
        with pytest.raises(Invalid):
            crt([1, 2], [3])

    def test_an_empty_system_is_refused(self):
        with pytest.raises(Invalid):
            crt([], [])

    def test_a_non_positive_modulus_is_refused(self):
        with pytest.raises(Invalid):
            crt([1], [0])
