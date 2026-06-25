"""Mathematics-research domain: discover closed forms for integer sequences.

Each instance is a sequence given by its first terms. The strategy proposes a
polynomial; the domain verifies it two ways:

* if the true closed form is a known polynomial and the candidate is *exactly*
  identical to it (checked over the rationals), the result is ``VERIFIED_SYMBOLIC``;
* otherwise, if the candidate reproduces the held-out terms, it is ``EMPIRICAL``.

Sequences that are not polynomial (powers of two, Fibonacci, factorial) cannot
be captured by a bounded-degree polynomial, and the harness reports them as
*not solved* rather than inventing a formula. A candidate that fits the fitted
terms but fails the held-out terms is likewise reported as not solved. This is
the domain's honesty guarantee: no closed form is ever reported unless it holds
on data the search never saw (or is provably identical to the truth).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable, Dict, List, Optional

from ..engine.evaluation import InstanceOutcome
from ..engine.genome import Genome
from ..engine.sandbox import Budget
from ..engine.schema import IntRange, ParamSpec, Toggle
from ..strategies import formula_search
from ..trusted.integrity import Claim, Evidence, assert_supported
from ..trusted.symbolic import coeffs_identical, poly_eval
from .base import Domain

_FIT_INDICES = list(range(0, 8))
_HOLDOUT_INDICES = [8, 9, 10, 11]


def _fib() -> Callable[[int], int]:
    cache = {0: 0, 1: 1}

    def f(n: int) -> int:
        if n not in cache:
            cache[n] = f(n - 1) + f(n - 2)
        return cache[n]

    return f


def _factorial(n: int) -> int:
    result = 1
    for k in range(2, n + 1):
        result *= k
    return result


def _format_poly(coeffs: List[Fraction]) -> str:
    terms = []
    for power, coeff in enumerate(coeffs):
        if coeff == 0:
            continue
        if power == 0:
            terms.append(str(coeff))
        elif power == 1:
            terms.append("{}*n".format(coeff))
        else:
            terms.append("{}*n^{}".format(coeff, power))
    return " + ".join(terms) if terms else "0"


def _degree(coeffs: List[Fraction]) -> int:
    deg = 0
    for power, coeff in enumerate(coeffs):
        if coeff != 0:
            deg = power
    return deg


class MathResearchDomain(Domain):
    name = "math"

    def __init__(self) -> None:
        fib = _fib()
        self._seqs: Dict[str, Callable[[int], int]] = {
            "const7": lambda n: 7,
            "linear_3n_2": lambda n: 3 * n + 2,
            "triangular": lambda n: n * (n + 1) // 2,
            "squares": lambda n: n * n,
            "quad_2n2_n_1": lambda n: 2 * n * n - n + 1,
            "cubic_n3": lambda n: n ** 3,
            "cubic_shift": lambda n: n ** 3 - 2 * n,
            "sum_cubes": lambda n: (n * (n + 1) // 2) ** 2,
            "quartic_n4": lambda n: n ** 4,
            "pow2": lambda n: 2 ** n,
            "fibonacci": fib,
            "factorial": _factorial,
        }
        # Exact rational coefficients for the genuinely polynomial sequences.
        self._true_poly: Dict[str, List[Fraction]] = {
            "const7": [Fraction(7)],
            "linear_3n_2": [Fraction(2), Fraction(3)],
            "triangular": [Fraction(0), Fraction(1, 2), Fraction(1, 2)],
            "squares": [Fraction(0), Fraction(0), Fraction(1)],
            "quad_2n2_n_1": [Fraction(1), Fraction(-1), Fraction(2)],
            "cubic_n3": [Fraction(0), Fraction(0), Fraction(0), Fraction(1)],
            "cubic_shift": [Fraction(0), Fraction(-2), Fraction(0), Fraction(1)],
            "sum_cubes": [Fraction(0), Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(1, 4)],
            "quartic_n4": [Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(1)],
        }

    def schema(self) -> Dict[str, ParamSpec]:
        return {
            "max_degree": IntRange(0, 6, 1),
            "parsimony": Toggle(),
        }

    def seed_genome(self) -> Genome:
        return Genome(
            domain=self.name,
            params={"max_degree": 0, "parsimony": True},
            notes="Deliberately weak seed: can only express constant sequences.",
        )

    def instance_ids(self) -> List[str]:
        return sorted(self._seqs)

    def complexity(self, genome: Genome) -> int:
        return int(genome.params["max_degree"])

    def evaluate(self, genome: Genome, instance_id: str, budget: Budget) -> InstanceOutcome:
        seq = self._seqs[instance_id]
        fit_points = [(n, seq(n)) for n in _FIT_INDICES]
        attempt = formula_search.search(fit_points, dict(genome.params), budget)

        if attempt.coeffs is None:
            return InstanceOutcome(
                instance_id=instance_id,
                claimed=False,
                verified=False,
                evidence=Evidence.CONJECTURE,
                cost=attempt.cost,
                integrity_ok=True,
                detail="no polynomial within degree cap {}".format(genome.params["max_degree"]),
                claim=None,
            )

        cand = attempt.coeffs
        holdout_fit = all(
            poly_eval(cand, Fraction(n)) == Fraction(seq(n)) for n in _HOLDOUT_INDICES
        )
        true_coeffs = self._true_poly.get(instance_id)
        symbolic_ok = true_coeffs is not None and coeffs_identical(cand, true_coeffs)
        # Ceiling derived from the verifier's checks, independent of the claim.
        if symbolic_ok:
            ceiling = Evidence.VERIFIED_SYMBOLIC
        elif holdout_fit:
            ceiling = Evidence.EMPIRICAL
        else:
            ceiling = Evidence.REFUTED

        if symbolic_ok:
            claim = Claim(
                statement="{}: a(n) = {}".format(instance_id, _format_poly(cand)),
                evidence=Evidence.VERIFIED_SYMBOLIC,
                detail="exact polynomial identity (degree {})".format(_degree(cand)),
                support=_degree(cand),
                verified=True,
            )
            assert_supported(claim, ceiling)
            return self._solved(instance_id, attempt.cost, Evidence.VERIFIED_SYMBOLIC, claim)

        if holdout_fit:
            claim = Claim(
                statement="{}: a(n) = {}".format(instance_id, _format_poly(cand)),
                evidence=Evidence.EMPIRICAL,
                detail="reproduces {} held-out terms".format(len(_HOLDOUT_INDICES)),
                support=len(_HOLDOUT_INDICES),
                verified=True,
            )
            assert_supported(claim, ceiling)
            return self._solved(instance_id, attempt.cost, Evidence.EMPIRICAL, claim)

        return InstanceOutcome(
            instance_id=instance_id,
            claimed=True,
            verified=False,
            evidence=Evidence.REFUTED,
            cost=attempt.cost,
            integrity_ok=True,
            detail="candidate fits fitted terms but fails held-out terms (overfit)",
            claim=None,
        )

    def _solved(self, instance_id, cost, evidence, claim) -> InstanceOutcome:
        return InstanceOutcome(
            instance_id=instance_id,
            claimed=True,
            verified=True,
            evidence=evidence,
            cost=cost,
            integrity_ok=True,
            detail=claim.detail,
            claim=claim,
        )
