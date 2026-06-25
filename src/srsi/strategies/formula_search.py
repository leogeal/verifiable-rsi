"""Evolvable closed-form search for the mathematics-research domain.

Given the first several terms of an integer sequence, the strategy looks for a
polynomial that reproduces them. It only ever *proposes* a polynomial; the
domain then checks it against held-out terms of the same sequence (and, when the
true closed form is known, against it exactly). A proposal that fits the fitted
terms but fails the held-out terms is honestly reported as not-solved -- the
harness never fabricates a formula it cannot stand behind.

Genome knobs:

* ``max_degree`` -- highest polynomial degree to consider. The dominant driver:
  a low cap can only express low-degree sequences.
* ``parsimony``  -- when True, return the *lowest*-degree polynomial consistent
  with the fitted terms; when False, interpolate through all fitted terms.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..engine.sandbox import Budget, BudgetExceeded
from ..trusted.symbolic import lagrange_interpolate, poly_eval


@dataclass(frozen=True)
class FormulaAttempt:
    coeffs: Optional[List[Fraction]]
    claimed: bool
    cost: int


def search(
    fit_points: Sequence[Tuple[int, int]], params: Dict, budget: Budget
) -> FormulaAttempt:
    max_degree = int(params["max_degree"])
    parsimony = bool(params["parsimony"])

    points = sorted((Fraction(n), Fraction(v)) for n, v in fit_points)
    cost = 0

    def fits_all(coeffs: List[Fraction]) -> bool:
        return all(poly_eval(coeffs, n) == v for n, v in points)

    try:
        if parsimony:
            for degree in range(0, max_degree + 1):
                budget.tick()
                cost += 1
                if len(points) < degree + 1:
                    break
                coeffs = lagrange_interpolate(points[: degree + 1])
                if fits_all(coeffs):
                    return FormulaAttempt(coeffs, True, cost)
            return FormulaAttempt(None, False, cost)
        else:
            budget.tick()
            cost += 1
            # Interpolate through every fitted point (degree = len-1), but only
            # accept if that degree is within the declared cap; otherwise the
            # strategy honestly cannot express it.
            if len(points) - 1 > max_degree:
                return FormulaAttempt(None, False, cost)
            coeffs = lagrange_interpolate(points)
            return FormulaAttempt(coeffs, True, cost)
    except BudgetExceeded:
        return FormulaAttempt(None, False, cost)
