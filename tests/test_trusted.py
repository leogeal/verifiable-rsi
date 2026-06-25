from fractions import Fraction

import pytest

from srsi.trusted.dimensions import (
    ENERGY,
    MASS,
    VELOCITY,
    Dim,
    terms_addable,
)
from srsi.trusted.holdout import assess_overfit, split
from srsi.trusted.integrity import (
    Claim,
    Evidence,
    OverclaimError,
    assert_supported,
    trusted_fingerprint,
)
from srsi.trusted.symbolic import (
    coeffs_identical,
    identical_univariate,
    lagrange_interpolate,
    poly_eval,
)


# --- integrity -----------------------------------------------------------

def test_evidence_ordering():
    assert Evidence.PROVED > Evidence.VERIFIED_SYMBOLIC > Evidence.EMPIRICAL
    assert Evidence.EMPIRICAL > Evidence.CONJECTURE > Evidence.REFUTED


def test_assert_supported_blocks_overclaim():
    claim = Claim("x", Evidence.PROVED, verified=True)
    with pytest.raises(OverclaimError):
        assert_supported(claim, Evidence.EMPIRICAL)
    # within ceiling is fine
    assert_supported(claim, Evidence.PROVED)


def test_trusted_fingerprint_is_stable_hex():
    fp1 = trusted_fingerprint()
    fp2 = trusted_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 64
    int(fp1, 16)  # parses as hex


# --- symbolic ------------------------------------------------------------

def test_identical_univariate():
    f = lambda x: x * x
    g = lambda x: poly_eval([Fraction(0), Fraction(0), Fraction(1)], x)
    assert identical_univariate(f, g, degree_bound=2)
    h = lambda x: x * x + 1
    assert not identical_univariate(f, h, degree_bound=2)


def test_lagrange_recovers_polynomial():
    pts = [(Fraction(0), Fraction(0)), (Fraction(1), Fraction(1)), (Fraction(2), Fraction(4))]
    coeffs = lagrange_interpolate(pts)
    assert coeffs_identical(coeffs, [Fraction(0), Fraction(0), Fraction(1)])


def test_coeffs_identical_ignores_trailing_zeros():
    assert coeffs_identical([Fraction(1), Fraction(2)], [Fraction(1), Fraction(2), Fraction(0)])


# --- dimensions ----------------------------------------------------------

def test_energy_dimension_algebra():
    assert MASS * VELOCITY.pow(2) == ENERGY


def test_terms_addable():
    assert terms_addable([ENERGY, ENERGY])
    assert not terms_addable([ENERGY, MASS])
    assert terms_addable([])


# --- holdout -------------------------------------------------------------

def test_split_is_deterministic_and_nonempty():
    ids = ["a", "b", "c", "d", "e"]
    s1, h1 = split(ids, holdout_frac=0.4, seed=0)
    s2, h2 = split(ids, holdout_frac=0.4, seed=0)
    assert (s1, h1) == (s2, h2)
    assert s1 and h1
    assert set(s1) | set(h1) == set(ids)
    assert not (set(s1) & set(h1))


def test_assess_overfit():
    clean = assess_overfit(0.9, 0.88, max_gap=0.15)
    assert not clean.is_overfit
    bad = assess_overfit(0.95, 0.50, max_gap=0.15)
    assert bad.is_overfit
