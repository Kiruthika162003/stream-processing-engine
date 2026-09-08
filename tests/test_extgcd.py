from __future__ import annotations

import math

import pytest

from rill.errors import Invalid
from rill.extgcd import extended_gcd, gcd, mod_inverse


class TestGcd:
    def test_it_matches_the_library_gcd(self):
        for a in range(120):
            for b in range(120):
                assert gcd(a, b) == math.gcd(a, b)

    def test_the_bezout_identity_holds(self):
        for a in range(1, 80):
            for b in range(1, 80):
                g, x, y = extended_gcd(a, b)
                assert a * x + b * y == g


class TestModInverse:
    def test_a_concrete_inverse(self):
        assert mod_inverse(3, 11) == 4  # 3 * 4 == 12 == 1 (mod 11)

    def test_it_matches_pythons_own_modular_inverse(self):
        for m in range(2, 60):
            for a in range(1, m):
                if math.gcd(a, m) == 1:
                    assert mod_inverse(a, m) == pow(a, -1, m)

    def test_the_inverse_multiplies_back_to_one(self):
        for m in range(2, 50):
            for a in range(1, m):
                if math.gcd(a, m) == 1:
                    assert a * mod_inverse(a, m) % m == 1


class TestRefusals:
    def test_a_non_coprime_pair_has_no_inverse(self):
        with pytest.raises(Invalid):
            mod_inverse(4, 8)

    def test_a_non_positive_modulus_is_refused(self):
        with pytest.raises(Invalid):
            mod_inverse(3, 0)
