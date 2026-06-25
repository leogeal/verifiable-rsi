"""Held-out evaluation splits and overfitting detection.

This is the anti-Goodhart machinery the research report kept pointing at: the
METR developer RCT (people *felt* 20% faster while being 19% slower) and DGM's
staged-subset caveat both say the same thing -- measure improvement on data the
optimiser never touched.

Instances are partitioned deterministically by hashing their ids with a seed,
so the split is reproducible and independent of evaluation order. The engine
fits and selects candidates on the *selection* ids and promotes based on the
*held-out* ids; a candidate that improves selection but regresses held-out is
flagged as overfitting and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import List, Sequence, Tuple


def _hash_unit(instance_id: str, seed: int) -> float:
    """Map an id to a stable pseudo-uniform value in [0, 1)."""

    digest = sha256("{}:{}".format(seed, instance_id).encode("utf-8")).hexdigest()
    # Use the first 8 hex digits as a 32-bit integer.
    return int(digest[:8], 16) / 0x100000000


def split(
    instance_ids: Sequence[str], holdout_frac: float = 0.4, seed: int = 0
) -> Tuple[List[str], List[str]]:
    """Partition ``instance_ids`` into (selection, holdout).

    Deterministic in ``seed``; order-independent. Guarantees at least one id on
    each side when there are >= 2 ids, so neither evaluation is empty.
    """

    if not 0.0 < holdout_frac < 1.0:
        raise ValueError("holdout_frac must be in (0, 1)")
    selection: List[str] = []
    holdout: List[str] = []
    for instance_id in instance_ids:
        if _hash_unit(instance_id, seed) < holdout_frac:
            holdout.append(instance_id)
        else:
            selection.append(instance_id)

    ordered = list(instance_ids)
    if len(ordered) >= 2:
        if not selection:
            selection.append(holdout.pop())
        if not holdout:
            holdout.append(selection.pop())
    return selection, holdout


@dataclass(frozen=True)
class OverfitReport:
    selection_score: float
    holdout_score: float
    gap: float
    is_overfit: bool

    def to_dict(self):
        return {
            "selection_score": round(self.selection_score, 6),
            "holdout_score": round(self.holdout_score, 6),
            "gap": round(self.gap, 6),
            "is_overfit": self.is_overfit,
        }


def assess_overfit(
    selection_score: float, holdout_score: float, max_gap: float = 0.15
) -> OverfitReport:
    """Flag a candidate whose selection score outruns its held-out score by
    more than ``max_gap``. The gap is the honest measure of how much the
    candidate exploited the selection set rather than generalising."""

    gap = selection_score - holdout_score
    return OverfitReport(
        selection_score=selection_score,
        holdout_score=holdout_score,
        gap=gap,
        is_overfit=gap > max_gap,
    )
