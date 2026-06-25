# Project Roadmap

Long-term goal: build toward a Fully-Recursive Self-Improving AGI/ASI System,
defined as a generally intelligent, and potentially superintelligent, system
that can safely improve its own improvement machinery while preserving
independent verification.

Current status: SRSI is a bounded, verifier-first scaffold-improvement harness.
It can improve task strategies, but it does not yet improve the proposer,
strategy source code, tools, benchmark machinery, sandbox policy, verifier, or
underlying model.

The unsolved status of open-ended model-level or weight-level recursive
self-improvement is not treated as evidence that it cannot be done. A
fully-recursive self-improving AGI/ASI system is the central research target for
this project. The roadmap is organized to make any claimed breakthrough
auditable: the project should move from bounded scaffold improvement toward
stronger recursive capabilities only with independent verification, sandboxing,
and human-gated authority control.

This roadmap lists practical milestones in the order they should be attempted.
Each milestone should land with tests and run artifacts that demonstrate both
successful improvement and contained failure.

## Non-Negotiable Constraints

- Trusted verifiers and promotion gates are not modified inside the same run
  that benefits from them.
- Generated or modified code does not execute in-process.
- A candidate never scores itself.
- Held-out evaluation remains independent of the optimizer.
- Authority expansion is human-gated and denied by default.
- Every run records enough artifacts to replay or audit the result.
- Unsolved tasks and rejected candidates are reported honestly.

## Milestone 0: Preserve The Current Baseline

Status: done, but must stay green.

Purpose: keep the existing SRSI behavior stable while adding more recursive
machinery.

TODO:

- [x] Maintain theorem, math, and physics domains.
- [x] Maintain evidence labels for proved, verified-symbolic, and empirical
  findings.
- [x] Maintain protected fingerprints for trusted verifier and enforcement
  code.
- [x] Maintain lineage verification.
- [ ] Add a CI or local verification command that runs tests and verifies all
  checked-in run artifacts.
- [ ] Add a short "current baseline" report generated from tests and saved
  runs.

Acceptance criteria:

- `python3 -m pytest` passes.
- `srsi.cli verify` succeeds for checked-in run directories.
- README claims match saved artifacts.

## Milestone 1: Reproducible Run Manifests

Purpose: make every run self-describing before adding nondeterministic or
model-backed proposals.

TODO:

- [ ] Add a `run_manifest.json` artifact.
- [ ] Record domain, seed, holdout split, budget, iterations, proposer type,
  schema, protected fingerprint, package version, command-line args, and
  timestamp.
- [ ] Record source fingerprints for untrusted strategy code separately from
  trusted verifier code.
- [ ] Extend `srsi.cli verify` to check the manifest, lineage chain, protected
  fingerprint, and artifact completeness.
- [ ] Add tests that detect a modified manifest, missing artifact, or mismatched
  fingerprint.

Acceptance criteria:

- A completed run can be audited from artifacts alone.
- Any edit to trusted code, lineage, or manifest is detected by `verify`.

## Milestone 2: Larger Benchmark Splits

Purpose: strengthen generalization pressure before making the optimizer more
capable.

TODO:

- [ ] Add explicit `selection`, `holdout`, and `report-only` split support.
- [ ] Add hidden or private-style benchmark files that are not used for
  candidate selection.
- [ ] Add regression suites from previously failed or rejected candidates.
- [ ] Add contamination checks where feasible, such as duplicate instance IDs or
  train/test overlap warnings.
- [ ] Add per-domain unsolved-task reports with stable machine-readable schema.

Acceptance criteria:

- A candidate can improve selection performance and still be rejected for
  held-out regression.
- Final reports distinguish selected, held-out, and report-only performance.

## Milestone 3: Archive Search

Purpose: move beyond a single hill-climbed lineage while keeping evaluation
bounded.

TODO:

- [ ] Add an archive data model for genomes, scores, parentage, novelty, and
  evidence summaries.
- [ ] Preserve multiple promoted and near-promoted variants.
- [ ] Add parent selection policies, such as best, novelty-biased, and
  domain-specialist sampling.
- [ ] Add archive artifact writing and verification.
- [ ] Add tests showing a useful branch is retained even when it is not the
  current global best.

Acceptance criteria:

- Runs can branch and still produce auditable lineage.
- Archive entries are reproducible and linked to evaluation artifacts.

## Milestone 4: Model-Backed Structured Proposer

Purpose: let a frozen model propose better structured edits without allowing
arbitrary code execution.

TODO:

- [ ] Implement `LLMProposer` behind an explicit opt-in flag.
- [ ] Require structured output that parses into existing genome schemas.
- [ ] Record prompt, model identifier, temperature, raw output, parsed edits,
  and parse failures.
- [ ] Reject edits with unknown parameters, invalid values, or schema changes.
- [ ] Add a deterministic fixture proposer for tests so CI does not require
  network or API access.
- [ ] Add tests for malformed model output, overclaiming candidates, and
  replayed proposals.

Acceptance criteria:

- Model-backed proposals can improve at least one domain under the same gates as
  deterministic proposals.
- Failed or malformed proposals are recorded and contained.
- Default runs remain offline and deterministic.

## Milestone 5: Meta-Evaluation Of Improvers

Purpose: measure whether a modified improver is better at producing future
improvements, not only whether one child genome scores higher.

TODO:

- [ ] Define an `ImproverSpec` that includes proposer settings, archive policy,
  mutation policy, and evaluation budget.
- [ ] Add benchmark episodes where an improver must produce improvements across
  multiple domains or seeds.
- [ ] Score improvers by downstream improvement, reliability, cost, and
  regression rate.
- [ ] Compare child improvers against parent improvers on held-out episodes.
- [ ] Add reports showing whether improvement ability compounds over
  generations.

Acceptance criteria:

- The system can promote an improver because it is better at creating future
  improvements.
- A single lucky candidate improvement is insufficient for meta-promotion.

## Milestone 6: Container Sandbox For Code Candidates

Purpose: establish the isolation boundary required before any generated or
modified code is executed.

TODO:

- [ ] Select a sandbox backend, such as container, VM, or restricted process
  runner.
- [ ] Disable network by default.
- [ ] Remove ambient credentials and secrets.
- [ ] Enforce CPU, memory, process, filesystem, and wall-clock limits.
- [ ] Mount inputs read-only and artifacts write-only.
- [ ] Capture stdout, stderr, exit code, resource usage, file diffs, and timeout
  reasons.
- [ ] Add tests for timeout, crash, excessive output, forbidden file write, and
  forbidden network attempt.

Acceptance criteria:

- Host project files and credentials are not writable or readable beyond the
  declared sandbox policy.
- Malicious or broken candidates fail closed and leave auditable artifacts.

## Milestone 7: Untrusted Strategy-Code Evolution

Purpose: allow candidates to modify untrusted strategy code while preserving the
trusted verifier boundary.

TODO:

- [ ] Define a patch format for candidate strategy changes.
- [ ] Restrict initial patches to `srsi/strategies` or a new untrusted
  candidate package.
- [ ] Run patched strategies only inside the sandbox.
- [ ] Re-run domain tests and held-out evaluations against patched candidates.
- [ ] Store patches as review artifacts before promotion.
- [ ] Add tests showing verifier changes are rejected or quarantined.

Acceptance criteria:

- A generated strategy-code patch can be evaluated and promoted without
  modifying trusted code.
- A patch that attempts to modify trusted verifiers, gates, or sandbox policy is
  blocked or sent to human review only.

## Milestone 8: Tool Improvement

Purpose: let the system improve tools used by the improvement loop without
letting tools silently change the grading standard.

TODO:

- [ ] Identify untrusted tools eligible for improvement, such as failure
  summarizers, testcase reducers, proof-search heuristics, and report analyzers.
- [ ] Add tool-specific tests independent from downstream candidate tests.
- [ ] Record whether a tool improvement changes proposal quality, evaluation
  cost, or debugging success.
- [ ] Keep benchmark scoring and trusted verification outside tool control.

Acceptance criteria:

- A tool change improves future search or analysis outcomes on held-out
  episodes.
- Tool changes cannot relax correctness criteria.

## Milestone 9: Human-Gated Authority Expansion

Purpose: separate capability gains from permissions.

TODO:

- [ ] Define authority levels for filesystem, network, dependency installation,
  model access, training, benchmark changes, and trusted-code changes.
- [ ] Add approval records for any authority expansion.
- [ ] Add CLI support for reviewing proposed privileged changes.
- [ ] Add durable logs of who approved what, when, and for which run.
- [ ] Add tests showing privileged changes are denied by default.

Acceptance criteria:

- A candidate can become more capable without automatically receiving more
  authority.
- Every authority expansion is explicit, reviewable, and replayable.

## Milestone 10: Long-Horizon Research Episodes

Purpose: test whether the system can improve over tasks closer to research
workflows, not only short benchmark instances.

TODO:

- [ ] Add multi-step episodes with intermediate artifacts.
- [ ] Add delayed-feedback tasks where early choices affect later success.
- [ ] Add cross-domain tasks that require planning, debugging, and tool use.
- [ ] Add report-only external evaluation suites.
- [ ] Track wall-clock cost, compute cost, and failure recovery.

Acceptance criteria:

- Later improver generations solve longer or more ambiguous episodes than early
  generations.
- Reports distinguish genuine task progress from benchmark-specific shortcuts.

## Milestone 11: Model-Level Recursion Research

Status: deferred until sandboxing, meta-evaluation, human approval, and
independent verification are mature. Deferred does not mean abandoned; this is
the milestone that directly targets model-level recursive self-improvement.

Purpose: investigate whether the underlying learning system can be improved by
the system itself, and produce credible evidence for or against that possibility
rather than assuming either answer.

TODO:

- [ ] Define isolated training or fine-tuning pipelines.
- [ ] Add data provenance and licensing checks.
- [ ] Add pre-training and post-training evaluation suites.
- [ ] Add safety and capability regression tests.
- [ ] Add rollback and quarantine mechanisms.
- [ ] Require explicit human approval before any trained model is used outside
  evaluation.

Acceptance criteria:

- There is independently verified evidence that a system improved the learning
  machinery that powers future improvements.
- Training changes cannot bypass safety, provenance, or deployment gates.

## Near-Term TODO

The next implementation sequence should be:

1. Add `run_manifest.json` and stronger `verify`.
2. Add richer benchmark split reporting.
3. Add archive data structures and artifacts.
4. Add a fixture-backed structured proposer interface.
5. Add optional model-backed structured proposals.
6. Add meta-evaluation episodes for improver variants.

Generated code execution, strategy-code patching, and model-level recursion
should wait until the required sandbox and authority controls exist.
