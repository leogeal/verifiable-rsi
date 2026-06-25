"""Physics-research domain: rediscover conserved quantities from trajectories.

Each instance is a simple mechanical system (harmonic oscillators and free-fall
motion with various parameters), supplied as sampled trajectories. The strategy
proposes a two-term invariant ``f1 + c*f2``; the domain verifies it stays
constant along *held-out* trajectories with different initial conditions, and
reports it at the ``EMPIRICAL`` level with its physical dimension. A quantity
that is constant only on the fitted trajectories is reported as not conserved.

The honest ceiling here is empirical: numerical constancy on unseen data is
strong evidence, but it is not a proof, and the harness never labels it as one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

from ..engine.evaluation import InstanceOutcome
from ..engine.genome import Genome
from ..engine.sandbox import Budget
from ..engine.schema import Categorical, ParamSpec
from ..strategies import invariant_search
from ..trusted.dimensions import Dim, LENGTH, VELOCITY, DIMENSIONLESS, terms_addable
from ..trusted.integrity import Claim, Evidence, assert_supported
from .base import Domain

_BASE_DIM = {"x": LENGTH, "v": VELOCITY, "h": LENGTH}

# The held-out constancy threshold is a FIXED, trusted constant -- never a genome
# parameter. The thing being judged must not get to set how strict its own grader
# is. Genuine invariants on these systems are constant to ~1e-13 relative; wrong
# combinations drift by >0.1, so this strict bound cleanly separates them.
_HOLDOUT_TOLERANCE = 1e-6


def _feature_dim(name: str) -> Dim:
    if name == "one":
        return DIMENSIONLESS
    if name in _BASE_DIM:
        return _BASE_DIM[name]
    if name.endswith("2") and name[:-1] in _BASE_DIM:
        return _BASE_DIM[name[:-1]].pow(2)
    if len(name) == 2 and name[0] in _BASE_DIM and name[1] in _BASE_DIM:
        return _BASE_DIM[name[0]] * _BASE_DIM[name[1]]
    raise KeyError("no dimension known for feature {!r}".format(name))


def _features(raw: Dict[str, float]) -> Dict[str, float]:
    feats = dict(raw)
    names = list(raw)
    for key, val in raw.items():
        feats[key + "2"] = val * val
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            feats[names[i] + names[j]] = raw[names[i]] * raw[names[j]]
    feats["one"] = 1.0
    return feats


def _oscillator_traj(m: float, k: float, amplitude: float, phase: float, n: int = 24):
    omega = math.sqrt(k / m)
    traj = []
    for i in range(n):
        t = i * 0.3
        x = amplitude * math.cos(omega * t + phase)
        v = -amplitude * omega * math.sin(omega * t + phase)
        traj.append(_features({"x": x, "v": v}))
    return traj


def _freefall_traj(g: float, v0: float, n: int = 24):
    traj = []
    for i in range(n):
        t = i * 0.08
        h = v0 * t - 0.5 * g * t * t
        v = v0 - g * t
        traj.append(_features({"h": h, "v": v}))
    return traj


@dataclass(frozen=True)
class _System:
    fit: List[List[Dict[str, float]]]
    holdout: List[List[Dict[str, float]]]


class PhysicsDomain(Domain):
    name = "physics"

    def __init__(self) -> None:
        self._systems: Dict[str, _System] = {
            "oscillator_unit": _System(
                fit=[
                    _oscillator_traj(1.0, 1.0, 1.0, 0.0),
                    _oscillator_traj(1.0, 1.0, 1.6, 0.5),
                    _oscillator_traj(1.0, 1.0, 0.7, 1.0),
                ],
                holdout=[
                    _oscillator_traj(1.0, 1.0, 2.1, 0.2),
                    _oscillator_traj(1.0, 1.0, 1.2, 2.0),
                ],
            ),
            "oscillator_heavy": _System(
                fit=[
                    _oscillator_traj(2.0, 1.0, 1.0, 0.0),
                    _oscillator_traj(2.0, 1.0, 1.4, 0.7),
                    _oscillator_traj(2.0, 1.0, 0.8, 1.3),
                ],
                holdout=[
                    _oscillator_traj(2.0, 1.0, 1.9, 0.3),
                    _oscillator_traj(2.0, 1.0, 1.1, 1.8),
                ],
            ),
            "freefall_slow": _System(
                fit=[
                    _freefall_traj(9.8, 5.0),
                    _freefall_traj(9.8, 7.0),
                    _freefall_traj(9.8, 4.0),
                ],
                holdout=[
                    _freefall_traj(9.8, 9.0),
                    _freefall_traj(9.8, 6.0),
                ],
            ),
            "freefall_fast": _System(
                fit=[
                    _freefall_traj(3.7, 8.0),
                    _freefall_traj(3.7, 11.0),
                    _freefall_traj(3.7, 6.0),
                ],
                holdout=[
                    _freefall_traj(3.7, 13.0),
                    _freefall_traj(3.7, 9.0),
                ],
            ),
            "oscillator_light": _System(
                fit=[
                    _oscillator_traj(0.5, 1.0, 1.0, 0.0),
                    _oscillator_traj(0.5, 1.0, 1.3, 0.9),
                    _oscillator_traj(0.5, 1.0, 0.6, 1.5),
                ],
                holdout=[
                    _oscillator_traj(0.5, 1.0, 1.8, 0.4),
                    _oscillator_traj(0.5, 1.0, 1.0, 2.2),
                ],
            ),
            "freefall_moon": _System(
                fit=[
                    _freefall_traj(1.6, 4.0),
                    _freefall_traj(1.6, 6.0),
                    _freefall_traj(1.6, 3.0),
                ],
                holdout=[
                    _freefall_traj(1.6, 7.0),
                    _freefall_traj(1.6, 5.0),
                ],
            ),
        }

    def schema(self) -> Dict[str, ParamSpec]:
        return {
            "candidate_features": Categorical(
                (
                    ("x", "v", "h"),
                    ("x2", "v2"),
                    ("v2", "h"),
                    ("x2", "v2", "h"),
                    ("x2", "v2", "h", "one"),
                    ("x2", "v2", "h2", "xv", "hv", "h", "x", "v", "one"),
                )
            ),
        }

    def seed_genome(self) -> Genome:
        return Genome(
            domain=self.name,
            params={"candidate_features": ("x", "v", "h")},
            notes="Deliberately weak seed: only linear features, no conserved pair.",
        )

    def instance_ids(self) -> List[str]:
        return sorted(self._systems)

    def complexity(self, genome: Genome) -> int:
        return len(genome.params["candidate_features"])

    def evaluate(self, genome: Genome, instance_id: str, budget: Budget) -> InstanceOutcome:
        system = self._systems[instance_id]
        features = genome.params["candidate_features"]

        attempt = invariant_search.fit(system.fit, features, budget)
        if attempt.pair is None:
            return InstanceOutcome(
                instance_id=instance_id,
                claimed=False,
                verified=False,
                evidence=Evidence.CONJECTURE,
                cost=attempt.cost,
                integrity_ok=True,
                detail="no usable feature pair for this system",
                claim=None,
            )

        f1, f2 = attempt.pair
        c = attempt.coeff
        conserved = self._constant_on(system.holdout, f1, f2, c, _HOLDOUT_TOLERANCE)
        # Ceiling is derived from what the verifier actually confirmed, so the
        # assert_supported guard below is real defence-in-depth, not a tautology.
        ceiling = Evidence.EMPIRICAL if conserved else Evidence.REFUTED

        if conserved:
            dim_f1 = _feature_dim(f1)
            dim_f2 = _feature_dim(f2)
            if terms_addable([dim_f1, dim_f2]):
                coeff_note = "dimensionless coefficient"
            else:
                coeff_note = "coefficient dimension {}".format(dim_f1 / dim_f2)
            claim = Claim(
                statement="{}: conserved {} + ({:.4g})*{}  [quantity {}; {}]".format(
                    instance_id, f1, c, f2, dim_f1, coeff_note
                ),
                evidence=Evidence.EMPIRICAL,
                detail="constant across {} held-out trajectories (fixed tol {:g})".format(
                    len(system.holdout), _HOLDOUT_TOLERANCE
                ),
                support=sum(len(traj) for traj in system.holdout),
                verified=True,
            )
            assert_supported(claim, ceiling)
            return InstanceOutcome(
                instance_id=instance_id,
                claimed=True,
                verified=True,
                evidence=Evidence.EMPIRICAL,
                cost=attempt.cost,
                integrity_ok=True,
                detail=claim.detail,
                claim=claim,
            )

        return InstanceOutcome(
            instance_id=instance_id,
            claimed=True,
            verified=False,
            evidence=Evidence.REFUTED,
            cost=attempt.cost,
            integrity_ok=True,
            detail="candidate {} + c*{} not constant on held-out trajectories".format(f1, f2),
            claim=None,
        )

    @staticmethod
    def _constant_on(trajectories, f1, f2, c, tol) -> bool:
        for traj in trajectories:
            values = [s[f1] + c * s[f2] for s in traj]
            if not values:
                return False
            spread = max(values) - min(values)
            scale = sum(abs(v) for v in values) / len(values) + 1e-9
            if spread / scale > tol:
                return False
        return True
