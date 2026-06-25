"""Dimensional analysis for the physics-research domain.

A dimension is a vector of exponents over the seven SI base dimensions, stored
as exact :class:`fractions.Fraction` values:

    (M mass, L length, T time, I current, THETA temperature, N amount, J luminous)

Two quantities can be added only if their dimensions match; :func:`terms_addable`
is the trusted check for that. Note carefully that a *conserved quantity* of the
form ``f1 + c*f2`` need NOT have ``f1`` and ``f2`` share a dimension: the
coefficient ``c`` is itself a dimensionful physical constant (for ``v^2 + 2g*h``
the constant ``2g`` carries acceleration, making both terms an energy per unit
mass). The physics domain therefore uses this module to *report* a discovered
invariant's dimensional structure -- the quantity's dimension, and whether the
fitted coefficient is dimensionless or dimensionful -- not to reject
differing-dimension terms. We deliberately do not claim a dimensional-rejection
guarantee the method cannot honestly provide.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Sequence, Tuple

_BASE_NAMES = ("M", "L", "T", "I", "THETA", "N", "J")


@dataclass(frozen=True)
class Dim:
    exps: Tuple[Fraction, Fraction, Fraction, Fraction, Fraction, Fraction, Fraction]

    @staticmethod
    def of(M=0, L=0, T=0, I=0, THETA=0, N=0, J=0) -> "Dim":
        return Dim(
            (
                Fraction(M),
                Fraction(L),
                Fraction(T),
                Fraction(I),
                Fraction(THETA),
                Fraction(N),
                Fraction(J),
            )
        )

    def __mul__(self, other: "Dim") -> "Dim":
        return Dim(tuple(a + b for a, b in zip(self.exps, other.exps)))

    def __truediv__(self, other: "Dim") -> "Dim":
        return Dim(tuple(a - b for a, b in zip(self.exps, other.exps)))

    def pow(self, k) -> "Dim":
        f = Fraction(k)
        return Dim(tuple(a * f for a in self.exps))

    def is_dimensionless(self) -> bool:
        return all(e == 0 for e in self.exps)

    def __str__(self) -> str:
        parts = [
            "{}^{}".format(name, exp)
            for name, exp in zip(_BASE_NAMES, self.exps)
            if exp != 0
        ]
        return "[" + (" ".join(parts) if parts else "1") + "]"


# Common dimensions, provided for convenience to the (trusted) domain code.
DIMENSIONLESS = Dim.of()
MASS = Dim.of(M=1)
LENGTH = Dim.of(L=1)
TIME = Dim.of(T=1)
VELOCITY = Dim.of(L=1, T=-1)
ACCELERATION = Dim.of(L=1, T=-2)
MOMENTUM = Dim.of(M=1, L=1, T=-1)
ENERGY = Dim.of(M=1, L=2, T=-2)
ANGULAR_MOMENTUM = Dim.of(M=1, L=2, T=-1)


def monomial_dim(base_dims: Dict[str, Dim], powers: Dict[str, int]) -> Dim:
    """Dimension of a monomial ``prod var**power`` given each variable's dim."""

    result = DIMENSIONLESS
    for var, power in powers.items():
        if var not in base_dims:
            raise KeyError("unknown variable {!r} in monomial".format(var))
        result = result * base_dims[var].pow(power)
    return result


def terms_addable(dims: Sequence[Dim]) -> bool:
    """True iff every dimension in ``dims`` is identical (so the terms may be
    summed into a single physical quantity). An empty list is trivially
    addable."""

    if not dims:
        return True
    first = dims[0]
    return all(d == first for d in dims)
