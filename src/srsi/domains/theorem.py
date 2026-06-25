"""Theorem-proving domain: refute propositional formulas, kernel-checked.

Every benchmark instance is a genuinely unsatisfiable clause set (confirmed by
the brute-force oracle at construction time). A genome earns credit on an
instance only when the trusted kernel verifies the strategy's refutation *and*
the oracle agrees the instance is truly unsatisfiable. A strategy that asserts a
proof the kernel rejects produces an integrity violation, which the engine
quarantines. Verified results carry the ``PROVED`` evidence level -- the only
domain that can.
"""

from __future__ import annotations

from itertools import product
from typing import Dict, List

from ..engine.evaluation import InstanceOutcome
from ..engine.genome import Genome
from ..engine.sandbox import Budget
from ..engine.schema import IntRange, ParamSpec, RealChoice, Toggle
from ..strategies import proof_search
from ..trusted.integrity import Claim, Evidence, assert_supported
from ..trusted.proof_kernel import Clause, is_unsat, verify_refutation
from .base import Domain


def _clause(*lits: int) -> Clause:
    return frozenset(lits)


def _all_k_clauses(variables: List[int]) -> List[Clause]:
    """Every full-length clause over ``variables`` -- a classic UNSAT set."""

    clauses = []
    for signs in product((1, -1), repeat=len(variables)):
        clauses.append(frozenset(sign * var for sign, var in zip(signs, variables)))
    return clauses


def _build_instances() -> Dict[str, List[Clause]]:
    instances: Dict[str, List[Clause]] = {
        "unit_contradiction": [_clause(1), _clause(-1)],
        "chain3": [_clause(1), _clause(-1, 2), _clause(-2, 3), _clause(-3)],
        "php_2_1": [_clause(1), _clause(2), _clause(-1, -2)],
        "all2": _all_k_clauses([1, 2]),
        "all3": _all_k_clauses([1, 2, 3]),
        "all3b": _all_k_clauses([4, 5, 6]),
        "all4": _all_k_clauses([1, 2, 3, 4]),
    }
    # Soundness of the benchmark itself: every instance must really be UNSAT.
    for name, clauses in instances.items():
        if not is_unsat(clauses):
            raise AssertionError("benchmark instance {!r} is not UNSAT".format(name))
    return instances


class TheoremDomain(Domain):
    name = "theorem"

    def __init__(self) -> None:
        self._instances = _build_instances()

    def schema(self) -> Dict[str, ParamSpec]:
        return {
            "w_len": RealChoice((0.0, 0.5, 1.0, 2.0)),
            "w_age": RealChoice((0.0, 0.25, 0.5, 1.0)),
            "max_len": IntRange(2, 6, 1),
            "use_sos": Toggle(),
            "trust_self_report": Toggle(),
        }

    def seed_genome(self) -> Genome:
        return Genome(
            domain=self.name,
            params={
                "w_len": 0.0,
                "w_age": 0.0,
                "max_len": 2,
                "use_sos": True,
                "trust_self_report": False,
            },
            notes="Deliberately weak seed: no heuristic, tight clause-length cap.",
        )

    def instance_ids(self) -> List[str]:
        return sorted(self._instances)

    def complexity(self, genome: Genome) -> int:
        return int(genome.params["max_len"])

    def evaluate(self, genome: Genome, instance_id: str, budget: Budget) -> InstanceOutcome:
        clauses = self._instances[instance_id]
        attempt = proof_search.search(clauses, dict(genome.params), budget)

        kernel_ok = False
        kernel_reason = "no proof emitted"
        if attempt.proof is not None:
            verdict = verify_refutation(clauses, attempt.proof)
            kernel_ok = verdict.ok
            kernel_reason = verdict.reason

        truly_unsat = is_unsat(clauses)
        verified = kernel_ok and truly_unsat
        # Ceiling derived from the verifier's own results, independent of the
        # claim, so assert_supported is genuine defence-in-depth.
        ceiling = Evidence.PROVED if verified else Evidence.REFUTED

        if attempt.claims_success and not verified:
            return InstanceOutcome(
                instance_id=instance_id,
                claimed=True,
                verified=False,
                evidence=Evidence.REFUTED,
                cost=attempt.cost,
                integrity_ok=False,
                detail="claimed success the kernel rejects: {}".format(kernel_reason),
                claim=None,
            )

        if verified:
            claim = Claim(
                statement="UNSAT({})".format(instance_id),
                evidence=Evidence.PROVED,
                detail="kernel-verified resolution refutation ({} steps)".format(
                    len(attempt.proof.steps)
                ),
                support=len(attempt.proof.steps),
                verified=True,
            )
            assert_supported(claim, ceiling)
            return InstanceOutcome(
                instance_id=instance_id,
                claimed=True,
                verified=True,
                evidence=Evidence.PROVED,
                cost=attempt.cost,
                integrity_ok=True,
                detail=claim.detail,
                claim=claim,
            )

        return InstanceOutcome(
            instance_id=instance_id,
            claimed=False,
            verified=False,
            evidence=Evidence.CONJECTURE,
            cost=attempt.cost,
            integrity_ok=True,
            detail="no proof found within budget",
            claim=None,
        )
