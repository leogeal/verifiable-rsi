"""The recursive self-improvement loop.

The loop is domain-agnostic. Each generation it:

1. re-checks the trusted verifier fingerprint (aborts on any change);
2. proposes one-step neighbour genomes of the current best;
3. scores each on the selection set and rejects any with integrity violations;
4. scores survivors on the held-out set and promotes the best one that improves
   held-out fitness without overfitting;
5. logs a tamper-evident lineage record.

When no candidate can be promoted, the search has converged and the loop stops.
The final report lists only verified findings (with their evidence levels) and
*explicitly names the instances it could not solve* -- the honesty contract is
that absence of a finding is reported, never hidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..domains.base import Domain
from ..trusted.holdout import OverfitReport, assess_overfit, split
from ..trusted.integrity import (
    EVIDENCE_LABEL,
    Evidence,
    OverclaimError,
    TamperError,
    protected_fingerprint,
)
from .evaluation import InstanceOutcome, Score, compute_score, verified_claims
from .gates import SafetyConfig, SafetyGate
from .genome import Genome
from .lineage import chain_hash
from .mutator import DeterministicProposer, Proposer
from .sandbox import Budget, BudgetExceeded


@dataclass(frozen=True)
class ImprovementRecord:
    iteration: int
    accepted: bool
    parent_id: str
    candidate_id: Optional[str]
    change: Optional[str]
    selection: Optional[Dict[str, Any]]
    holdout: Optional[Dict[str, Any]]
    overfit: Optional[Dict[str, Any]]
    reasons: Tuple[str, ...]
    prev_hash: str
    record_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "accepted": self.accepted,
            "parent_id": self.parent_id,
            "candidate_id": self.candidate_id,
            "change": self.change,
            "selection": self.selection,
            "holdout": self.holdout,
            "overfit": self.overfit,
            "reasons": list(self.reasons),
            "prev_hash": self.prev_hash,
            "record_hash": self.record_hash,
        }


@dataclass(frozen=True)
class RunResult:
    domain: str
    best_genome: Genome
    best_selection: Score
    best_holdout: Score
    records: Tuple[ImprovementRecord, ...]
    findings: Tuple[Dict[str, Any], ...]
    unsolved: Tuple[str, ...]
    evidence_breakdown: Dict[str, int]
    counters: Dict[str, int]
    integrity_events: Tuple[Dict[str, Any], ...]
    stopped_reason: str
    protected_fingerprint: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "best_genome": self.best_genome.to_dict(),
            "best_selection": self.best_selection.to_dict(),
            "best_holdout": self.best_holdout.to_dict(),
            "findings": list(self.findings),
            "unsolved": list(self.unsolved),
            "evidence_breakdown": self.evidence_breakdown,
            "counters": self.counters,
            "integrity_events": list(self.integrity_events),
            "stopped_reason": self.stopped_reason,
            "protected_fingerprint": self.protected_fingerprint,
            "records": [r.to_dict() for r in self.records],
        }


class RecursiveImprover:
    def __init__(
        self,
        domain: Domain,
        proposer: Proposer = None,
        gate: SafetyGate = None,
        budget_steps: int = 300,
        holdout_frac: float = 0.4,
        seed: int = 0,
        complexity_penalty: float = 0.002,
    ):
        self.domain = domain
        self.gate = gate or SafetyGate()
        self.proposer = proposer or DeterministicProposer(domain.schema())
        self.budget_steps = budget_steps
        self.complexity_penalty = complexity_penalty
        self.selection_ids, self.holdout_ids = split(domain.instance_ids(), holdout_frac, seed)

    # -- evaluation -------------------------------------------------------

    def _evaluate_set(
        self, genome: Genome, ids: Sequence[str]
    ) -> Tuple[Score, List[InstanceOutcome]]:
        complexity = self.domain.complexity(genome)
        outcomes: List[InstanceOutcome] = []
        for instance_id in ids:
            budget = Budget(self.budget_steps)
            try:
                outcome = self.domain.evaluate(genome, instance_id, budget)
            except OverclaimError as exc:
                outcome = InstanceOutcome(
                    instance_id=instance_id,
                    claimed=True,
                    verified=False,
                    evidence=Evidence.REFUTED,
                    cost=budget.used,
                    integrity_ok=False,
                    detail="overclaim blocked: {}".format(exc),
                    claim=None,
                )
            except BudgetExceeded:
                outcome = InstanceOutcome(
                    instance_id=instance_id,
                    claimed=False,
                    verified=False,
                    evidence=Evidence.CONJECTURE,
                    cost=self.budget_steps,
                    integrity_ok=True,
                    detail="budget exceeded",
                    claim=None,
                )
            outcomes.append(outcome)
        score = compute_score(outcomes, complexity, self.complexity_penalty, self.budget_steps)
        return score, outcomes

    # -- main loop --------------------------------------------------------

    def run(self, iterations: int, out_dir: Path = None) -> RunResult:
        baseline_fp = protected_fingerprint()
        current = self.domain.seed_genome()
        cur_sel, _ = self._evaluate_set(current, self.selection_ids)
        cur_hold, _ = self._evaluate_set(current, self.holdout_ids)

        records: List[ImprovementRecord] = []
        prev_hash = ""
        counters = {
            "candidates_evaluated": 0,
            "rejected_structure": 0,
            "rejected_integrity": 0,
            "rejected_holdout_regress": 0,
            "rejected_no_gain": 0,
            "promotions": 0,
        }
        integrity_events: List[Dict[str, Any]] = []
        stopped_reason = "iteration limit reached"

        for iteration in range(1, iterations + 1):
            if protected_fingerprint() != baseline_fp:
                raise TamperError(
                    "integrity-critical core changed during the run "
                    "(baseline {} != now {})".format(baseline_fp[:12], protected_fingerprint()[:12])
                )

            candidates = self.proposer.propose(current)
            candidates = candidates[: self.gate.config.max_candidates_per_iteration]
            scored = []
            gen_rejects = {"structure": 0, "integrity": 0, "holdout_regress": 0, "no_gain": 0}

            for candidate in candidates:
                counters["candidates_evaluated"] += 1
                structure = self.gate.validate_structure(candidate.genome, self.domain.schema())
                if not structure.accepted:
                    counters["rejected_structure"] += 1
                    gen_rejects["structure"] += 1
                    continue

                sel_score, _ = self._evaluate_set(candidate.genome, self.selection_ids)
                integrity = self.gate.validate_integrity(sel_score)
                if not integrity.accepted:
                    counters["rejected_integrity"] += 1
                    gen_rejects["integrity"] += 1
                    integrity_events.append(
                        {
                            "iteration": iteration,
                            "genome_id": candidate.genome.genome_id,
                            "change": "{}={}".format(candidate.changed_key, candidate.changed_value),
                            "reason": integrity.reasons[0],
                        }
                    )
                    continue

                hold_score, _ = self._evaluate_set(candidate.genome, self.holdout_ids)
                # The honesty gate runs on BOTH splits: a candidate that claims
                # an unverified success on any held-out instance is quarantined too.
                integrity_h = self.gate.validate_integrity(hold_score)
                if not integrity_h.accepted:
                    counters["rejected_integrity"] += 1
                    gen_rejects["integrity"] += 1
                    integrity_events.append(
                        {
                            "iteration": iteration,
                            "genome_id": candidate.genome.genome_id,
                            "change": "{}={}".format(candidate.changed_key, candidate.changed_value),
                            "reason": "held-out " + integrity_h.reasons[0],
                        }
                    )
                    continue

                overfit = assess_overfit(
                    sel_score.accuracy, hold_score.accuracy, self.gate.config.max_overfit_gap
                )
                promotion = self.gate.validate_promotion(
                    cur_sel, sel_score, cur_hold, hold_score
                )
                if not promotion.accepted:
                    if any("regressed" in reason for reason in promotion.reasons):
                        counters["rejected_holdout_regress"] += 1
                        gen_rejects["holdout_regress"] += 1
                    else:
                        counters["rejected_no_gain"] += 1
                        gen_rejects["no_gain"] += 1
                    continue

                scored.append((candidate, sel_score, hold_score, overfit))

            if not scored:
                stopped_reason = (
                    "converged: no candidate passed the integrity, overfit, "
                    "and promotion gates"
                )
                records.append(
                    self._make_record(
                        iteration, False, current.genome_id, None, None,
                        cur_sel, cur_hold, None,
                        (stopped_reason, _reject_summary(gen_rejects)), prev_hash,
                    )
                )
                prev_hash = records[-1].record_hash
                break

            best = max(
                scored,
                key=lambda s: (
                    s[1].fitness,        # selection fitness drives progress
                    s[1].accuracy,
                    s[2].accuracy,        # held-out accuracy breaks ties
                    -s[1].mean_cost,
                    s[0].genome.genome_id,
                ),
            )
            candidate, sel_score, hold_score, overfit = best
            counters["promotions"] += 1
            records.append(
                self._make_record(
                    iteration, True, current.genome_id, candidate.genome.genome_id,
                    "{}={}".format(candidate.changed_key, candidate.changed_value),
                    sel_score, hold_score, overfit.to_dict(),
                    (_reject_summary(gen_rejects),), prev_hash,
                )
            )
            prev_hash = records[-1].record_hash
            current = candidate.genome
            cur_sel = sel_score
            cur_hold = hold_score

        result = self._finalize(
            current, cur_sel, cur_hold, records, counters, integrity_events,
            stopped_reason, baseline_fp,
        )
        if out_dir is not None:
            self._write_artifacts(out_dir, result)
        return result

    # -- helpers ----------------------------------------------------------

    def _make_record(
        self, iteration, accepted, parent_id, candidate_id, change,
        selection, holdout, overfit, reasons, prev_hash,
    ) -> ImprovementRecord:
        payload = {
            "iteration": iteration,
            "accepted": accepted,
            "parent_id": parent_id,
            "candidate_id": candidate_id,
            "change": change,
            "selection": selection.to_dict() if selection is not None else None,
            "holdout": holdout.to_dict() if holdout is not None else None,
            "overfit": overfit,
            "reasons": list(reasons),
        }
        record_hash = chain_hash(prev_hash, payload)
        return ImprovementRecord(
            iteration=iteration,
            accepted=accepted,
            parent_id=parent_id,
            candidate_id=candidate_id,
            change=change,
            selection=payload["selection"],
            holdout=payload["holdout"],
            overfit=overfit,
            reasons=tuple(reasons),
            prev_hash=prev_hash,
            record_hash=record_hash,
        )

    def _finalize(
        self, current, cur_sel, cur_hold, records, counters, integrity_events,
        stopped_reason, baseline_fp,
    ) -> RunResult:
        # Re-check the protected core BEFORE recomputing and publishing findings,
        # so the verifiers that produce the final report are proven unchanged
        # since the run began -- closing the window after the last in-loop check.
        if protected_fingerprint() != baseline_fp:
            raise TamperError(
                "integrity-critical core changed before finalization "
                "(baseline {} != now {})".format(baseline_fp[:12], protected_fingerprint()[:12])
            )
        _, out_sel = self._evaluate_set(current, self.selection_ids)
        _, out_hold = self._evaluate_set(current, self.holdout_ids)
        all_outcomes = out_sel + out_hold

        findings = [claim.to_dict() for claim in verified_claims(all_outcomes)]
        unsolved = sorted(o.instance_id for o in all_outcomes if not o.verified)

        breakdown: Dict[str, int] = {}
        for outcome in all_outcomes:
            if outcome.verified:
                label = EVIDENCE_LABEL[outcome.evidence]
                breakdown[label] = breakdown.get(label, 0) + 1

        return RunResult(
            domain=self.domain.name,
            best_genome=current,
            best_selection=cur_sel,
            best_holdout=cur_hold,
            records=tuple(records),
            findings=tuple(findings),
            unsolved=tuple(unsolved),
            evidence_breakdown=breakdown,
            counters=counters,
            integrity_events=tuple(integrity_events),
            stopped_reason=stopped_reason,
            protected_fingerprint=baseline_fp,
        )

    def _write_artifacts(self, out_dir: Path, result: RunResult) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "lineage.jsonl").write_text(
            "".join(json.dumps(r.to_dict(), sort_keys=True) + "\n" for r in result.records),
            encoding="utf-8",
        )
        _write_json(out_dir / "best_genome.json", result.best_genome.to_dict())
        _write_json(out_dir / "findings.json", {
            "domain": result.domain,
            "findings": list(result.findings),
            "unsolved": list(result.unsolved),
            "evidence_breakdown": result.evidence_breakdown,
        })
        _write_json(out_dir / "run_summary.json", {
            "created_at": datetime.now(timezone.utc).isoformat(),
            **result.to_dict(),
        })


def _reject_summary(gen_rejects: Dict[str, int]) -> str:
    return "rejected this generation: structure={structure} integrity={integrity} " \
           "holdout_regress={holdout_regress} no_gain={no_gain}".format(**gen_rejects)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
