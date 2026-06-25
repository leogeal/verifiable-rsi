"""The gates a candidate must pass before it is promoted.

Three independent checks, in order of severity:

1. **Structure** -- every parameter is present and within its schema. A
   malformed genome never runs.
2. **Integrity** -- the candidate produced zero integrity violations on the
   selection set. A single instance where the strategy claimed a success the
   verifier denied disqualifies the whole candidate. This is the
   non-negotiable honesty gate.
3. **Promotion** -- progress is driven by the *selection* set (fitness must
   improve), while the *held-out* set is the anti-overfit guard: held-out
   accuracy must not regress. This is the standard train/validate discipline --
   optimise on training, but refuse any change that wins on training by losing
   on data it never saw.

A note on overfitting signals: the absolute selection-vs-held-out accuracy *gap*
is NOT used to gate, because instances are not i.i.d. -- the two buckets can have
different difficulty mixes, so a large gap may just mean "the hard instances
happen to be in one bucket," not overfitting. The honest overfit guards are
(a) held-out non-regression here, and (b) the per-instance held-out check inside
each domain's ``verified`` (a formula that fits the fitted terms but fails the
held-out terms of the same instance never counts as solved). The gap is still
computed and logged for transparency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .evaluation import Score
from .genome import Genome
from .schema import ParamSpec


@dataclass(frozen=True)
class GateDecision:
    accepted: bool
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class SafetyConfig:
    min_gain: float = 1e-6
    max_overfit_gap: float = 0.25
    allowed_holdout_accuracy_regression: float = 0.0
    max_candidates_per_iteration: int = 64


class SafetyGate:
    def __init__(self, config: SafetyConfig = None):
        self.config = config or SafetyConfig()

    def validate_structure(self, genome: Genome, schema: Dict[str, ParamSpec]) -> GateDecision:
        reasons = []
        for key, spec in schema.items():
            if key not in genome.params:
                reasons.append("missing parameter {!r}".format(key))
            elif not spec.is_valid(genome.params[key]):
                reasons.append("invalid value for {!r}: {!r}".format(key, genome.params[key]))
        unknown = set(genome.params) - set(schema)
        if unknown:
            reasons.append("unknown parameters: {}".format(sorted(unknown)))
        return GateDecision(not reasons, tuple(reasons))

    def validate_integrity(self, selection_score: Score) -> GateDecision:
        if selection_score.integrity_violations > 0:
            return GateDecision(
                False,
                (
                    "integrity violation: {} instance(s) claimed a success the "
                    "verifier rejected".format(selection_score.integrity_violations),
                ),
            )
        return GateDecision(True, ())

    def validate_promotion(
        self,
        parent_selection: Score,
        candidate_selection: Score,
        parent_holdout: Score,
        candidate_holdout: Score,
    ) -> GateDecision:
        reasons = []
        gain = candidate_selection.fitness - parent_selection.fitness
        if gain < self.config.min_gain:
            reasons.append(
                "selection fitness gain {:.6f} below required {:.6f}".format(
                    gain, self.config.min_gain
                )
            )
        floor = parent_holdout.accuracy - self.config.allowed_holdout_accuracy_regression
        if candidate_holdout.accuracy < floor:
            reasons.append(
                "held-out accuracy regressed from {:.3f} to {:.3f} (overfit guard)".format(
                    parent_holdout.accuracy, candidate_holdout.accuracy
                )
            )
        return GateDecision(not reasons, tuple(reasons))
