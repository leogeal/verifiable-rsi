"""Evolvable conserved-quantity search for the physics-research domain.

Given sampled trajectories of a dynamical system, the strategy looks for a
two-term combination ``f1 + c*f2`` of state features that stays constant along
each trajectory. It fits ``c`` on the *fit* trajectories by minimising the
within-trajectory variance (the closed-form least-squares solution), and returns
the best-fitting feature pair. The domain then re-checks that pair on *held-out*
trajectories with different initial conditions; an invariant that holds only on
the data it was fitted to is rejected as not conserved.

Conserved quantities here are reported at the ``EMPIRICAL`` evidence level --
numerical constancy on unseen trajectories, never "proved". That is the honest
ceiling for this method.

Genome knobs:

* ``candidate_features`` -- the set of state features the search may combine.
* ``tol`` -- relative-constancy tolerance (used by the domain when verifying).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..engine.sandbox import Budget, BudgetExceeded

Sample = Dict[str, float]
Trajectory = List[Sample]


@dataclass(frozen=True)
class InvariantAttempt:
    pair: Optional[Tuple[str, str]]
    coeff: float
    residual: float
    cost: int


def _centered(values_by_traj: List[List[float]]) -> List[float]:
    """Subtract each trajectory's mean and pool the residuals."""

    pooled: List[float] = []
    for series in values_by_traj:
        if not series:
            continue
        mean = sum(series) / len(series)
        pooled.extend(v - mean for v in series)
    return pooled


def fit(
    fit_trajectories: Sequence[Trajectory], candidate_features: Sequence[str], budget: Budget
) -> InvariantAttempt:
    usable = [
        f
        for f in candidate_features
        if all(f in sample for traj in fit_trajectories for sample in traj)
    ]
    cost = 0
    best: Optional[InvariantAttempt] = None

    try:
        for a in range(len(usable)):
            for b in range(a + 1, len(usable)):
                budget.tick()
                cost += 1
                f1, f2 = usable[a], usable[b]
                d1 = _centered([[s[f1] for s in traj] for traj in fit_trajectories])
                d2 = _centered([[s[f2] for s in traj] for traj in fit_trajectories])
                var2 = sum(y * y for y in d2)
                if var2 <= 1e-12:
                    continue  # degenerate: f2 does not vary
                cov = sum(x * y for x, y in zip(d1, d2))
                c = -cov / var2
                residual = sum((x + c * y) ** 2 for x, y in zip(d1, d2))
                # Normalise by the spread of f1 so residuals are comparable across pairs.
                scale = sum(x * x for x in d1)
                rel = residual / scale if scale > 1e-12 else residual
                if best is None or rel < best.residual:
                    best = InvariantAttempt((f1, f2), c, rel, cost)
    except BudgetExceeded:
        pass

    if best is None:
        return InvariantAttempt(None, 0.0, float("inf"), cost)
    return InvariantAttempt(best.pair, best.coeff, best.residual, cost)
