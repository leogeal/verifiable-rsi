"""Outcome and score types shared by every domain.

The distinction that makes the harness honest lives in :class:`InstanceOutcome`:

* ``claimed``  -- what the (evolvable, untrusted) strategy asserted.
* ``verified`` -- what the (fixed, trusted) verifier independently confirmed.
* ``integrity_ok`` -- ``False`` exactly when the strategy claimed a success the
  verifier denies. That is the signature of reward hacking, and the engine
  quarantines any candidate that produces it.

Accuracy is always computed from ``verified`` -- never from ``claimed`` -- so a
strategy cannot raise its own score by asserting success.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from ..trusted.integrity import Claim, Evidence


@dataclass(frozen=True)
class InstanceOutcome:
    instance_id: str
    claimed: bool
    verified: bool
    evidence: Evidence
    cost: int
    integrity_ok: bool
    detail: str
    claim: Optional[Claim] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "claimed": self.claimed,
            "verified": self.verified,
            "evidence": int(self.evidence),
            "cost": self.cost,
            "integrity_ok": self.integrity_ok,
            "detail": self.detail,
            "claim": self.claim.to_dict() if self.claim is not None else None,
        }


@dataclass(frozen=True)
class Score:
    total: int
    verified: int
    accuracy: float
    integrity_violations: int
    mean_cost: float
    fitness: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "verified": self.verified,
            "accuracy": round(self.accuracy, 6),
            "integrity_violations": self.integrity_violations,
            "mean_cost": round(self.mean_cost, 3),
            "fitness": round(self.fitness, 6),
        }


def compute_score(
    outcomes: Sequence[InstanceOutcome],
    complexity: int,
    complexity_penalty: float,
    cost_budget: int,
) -> Score:
    """Aggregate per-instance outcomes into a single score.

    ``accuracy`` counts only verified solves. ``fitness`` subtracts a small
    parsimony penalty (genome complexity) and an even smaller efficiency penalty
    (mean verified cost), so ties break toward simpler, faster strategies -- but
    correctness dominates. Integrity violations are reported here and enforced
    by the gate; a candidate with any violation is rejected outright regardless
    of fitness.
    """

    total = len(outcomes)
    verified = sum(1 for o in outcomes if o.verified)
    integrity_violations = sum(1 for o in outcomes if not o.integrity_ok)
    accuracy = verified / total if total else 0.0

    solved_costs = [o.cost for o in outcomes if o.verified]
    mean_cost = sum(solved_costs) / len(solved_costs) if solved_costs else 0.0
    cost_term = (mean_cost / cost_budget) if cost_budget > 0 else 0.0

    fitness = accuracy - complexity_penalty * complexity - 0.01 * cost_term
    return Score(
        total=total,
        verified=verified,
        accuracy=accuracy,
        integrity_violations=integrity_violations,
        mean_cost=mean_cost,
        fitness=fitness,
    )


def verified_claims(outcomes: Sequence[InstanceOutcome]) -> List[Claim]:
    """The honest findings: claims the trusted verifier actually confirmed."""

    return [o.claim for o in outcomes if o.verified and o.claim is not None]
