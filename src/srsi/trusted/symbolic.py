"""Exact symbolic verification for the mathematics-research domain.

Polynomials over the rationals are represented by their coefficient list,
``coeffs[k]`` being the coefficient of ``x**k``. The key trusted fact this
module relies on:

    Two polynomials of degree <= D that agree at D+1 distinct points are
    identical.

So :func:`identical_univariate` evaluates both polynomials at D+1 distinct
points using exact :class:`fractions.Fraction` arithmetic. There is no
floating-point error and no probabilistic gap. The soundness PRECONDITION is
that *both* inputs are polynomials of degree <= ``degree_bound``; the caller
must guarantee it, because the theorem fails if either input exceeds the bound
(a higher-degree function can coincide at the sampled points). For this reason
the mathematics domain does not rely on it for its verdict: it verifies a
discovered closed form by *exact coefficient comparison* against the known true
polynomial (:func:`coeffs_identical`), which needs no degree assumption, and
falls back to held-out evaluation otherwise.

:func:`lagrange_interpolate` is a convenience used by search strategies to
*propose* a polynomial through given points; it is not part of the trust
argument (the verifier re-checks any proposal), but it lives here because it is
pure and exact.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable, List, Sequence, Tuple

Rational = Fraction


def poly_eval(coeffs: Sequence[Rational], x: Rational) -> Rational:
    """Evaluate a polynomial (given by ascending coefficients) at ``x``."""

    acc = Fraction(0)
    for coeff in reversed(list(coeffs)):
        acc = acc * x + coeff
    return acc


def identical_univariate(
    f: Callable[[Rational], Rational],
    g: Callable[[Rational], Rational],
    degree_bound: int,
) -> bool:
    """Return True iff ``f == g`` as polynomials of degree <= ``degree_bound``.

    Evaluates both at ``degree_bound + 1`` distinct integer points with exact
    rational arithmetic. PRECONDITION: both ``f`` and ``g`` must be polynomials
    of degree <= ``degree_bound``. The result is exact under that precondition
    and is NOT sound if a caller passes a higher-degree or non-polynomial
    function (which may coincide at the sampled points).
    """

    if degree_bound < 0:
        raise ValueError("degree_bound must be non-negative")
    for point in range(degree_bound + 1):
        x = Fraction(point)
        if f(x) != g(x):
            return False
    return True


def coeffs_identical(a: Sequence[Rational], b: Sequence[Rational]) -> bool:
    """Exact equality of two coefficient lists, ignoring trailing zeros."""

    aa = _trim(a)
    bb = _trim(b)
    return aa == bb


def _trim(coeffs: Sequence[Rational]) -> List[Rational]:
    out = [Fraction(c) for c in coeffs]
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def lagrange_interpolate(points: Sequence[Tuple[Rational, Rational]]) -> List[Rational]:
    """Return ascending coefficients of the unique minimal-degree polynomial
    through ``points`` (distinct x-values), using exact rational arithmetic.

    Implemented by summing Lagrange basis polynomials. Raises if any two
    x-values coincide.
    """

    xs = [Fraction(x) for x, _ in points]
    ys = [Fraction(y) for _, y in points]
    if len(set(xs)) != len(xs):
        raise ValueError("interpolation points must have distinct x-values")

    result = [Fraction(0)]
    for i in range(len(points)):
        # Build basis_i(x) = prod_{j != i} (x - xs[j]) / (xs[i] - xs[j]).
        basis = [Fraction(1)]
        denom = Fraction(1)
        for j in range(len(points)):
            if j == i:
                continue
            basis = _poly_mul(basis, [-xs[j], Fraction(1)])
            denom *= xs[i] - xs[j]
        scale = ys[i] / denom
        term = [c * scale for c in basis]
        result = _poly_add(result, term)
    return _trim(result)


def _poly_mul(a: Sequence[Rational], b: Sequence[Rational]) -> List[Rational]:
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    return out


def _poly_add(a: Sequence[Rational], b: Sequence[Rational]) -> List[Rational]:
    n = max(len(a), len(b))
    out = []
    for k in range(n):
        av = a[k] if k < len(a) else Fraction(0)
        bv = b[k] if k < len(b) else Fraction(0)
        out.append(av + bv)
    return out
