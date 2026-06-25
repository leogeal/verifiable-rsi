# Fully-Recursive Self-Improvement Criteria

The long-term goal of SRSI is a Fully-Recursive Self-Improving system. SRSI is
currently a bounded scaffold-improvement harness: it repeatedly improves task
strategies, but the machinery that performs improvement is mostly fixed. To
honestly call a future system "Fully-recursive Self-Improvement," it would need
to improve the improver itself, not only the artifacts produced by the improver.

This document defines the target and the engineering evidence required to claim
progress toward it. The ordered implementation milestones are tracked in
[`../ROADMAP.md`](../ROADMAP.md).

The lack of a public verified demonstration of open-ended weight-level
recursive self-improvement is not taken as proof that such a system cannot be
built. It is one of the central open problems the project is intended to study.
The goal is to make claims about that possibility only through measured,
auditable breakthroughs rather than assumption or analogy.

## Working Definition

Fully-recursive self-improvement means:

> A system can safely improve its own improvement machinery, demonstrate that
> those changes generalize, and preserve independent verification while doing
> so.

The important word is "machinery." A loop that only tunes task-level parameters
is recursive in a limited sense, but it is not fully recursive. A fully
recursive system must be able to improve the processes that search, propose,
test, verify, debug, and promote future improvements.

## Current State

The current project improves strategy genomes interpreted by fixed code. That
means these components are fixed during a run:

- proposer implementation;
- mutation schema;
- strategy source code;
- benchmark definitions;
- trusted verifiers;
- promotion gates;
- sandbox policy;
- underlying model or reasoning engine.

That design is intentionally conservative. It gives the project deterministic
runs, bounded execution, clear verifier boundaries, and auditable artifacts.
It also means the current system is scaffold-recursive, not fully recursive.

## Required Capabilities

### 1. Mutable Proposer

The system should improve how it generates candidate improvements. This includes
changes to prompt construction, search heuristics, candidate ranking, failure
analysis, parent selection, and proposal diversity.

Evidence required:

- later proposer versions find valid improvements that earlier versions miss;
- proposer changes generalize across domains or hidden task suites;
- failed proposer changes are captured and rejected without corrupting the run.

### 2. Mutable Strategy Code

The system should be able to propose new algorithms or code patches, not only
parameter changes. This should begin with untrusted strategy code, not trusted
verifiers or gates.

Evidence required:

- generated or modified code runs only in a sandbox;
- candidate patches are reproducible from recorded artifacts;
- promotion depends on held-out performance and integrity checks;
- code that crashes, hangs, cheats, or overfits is contained.

### 3. Meta-Evaluation

The system should measure whether a new improver is better at producing future
improvements, not only whether a single child candidate scores higher.

Evidence required:

- evaluate improver variants over multiple downstream improvement episodes;
- compare against the parent improver on hidden tasks;
- account for cost, reliability, and regression rate;
- show that improvements compound over generations.

### 4. Archive Search

A fully recursive system should keep a population or archive of improver
variants rather than a single promoted lineage.

Evidence required:

- preserve diverse high-performing branches;
- sample parents by performance, novelty, and relevance;
- reuse discoveries across branches;
- avoid losing specialized capabilities due to one global fitness score.

### 5. Tool Improvement

The system should be able to improve supporting tools used by the improvement
loop, such as test generators, reducers, debuggers, theorem-proving heuristics,
experiment runners, and report analyzers.

Evidence required:

- tool changes improve future search or verification outcomes;
- tool changes are tested independently from the candidate they benefit;
- tool changes do not silently alter grading standards.

### 6. Generalization Pressure

The system must show that improvements transfer beyond the data used to select
them.

Evidence required:

- hidden held-out tests;
- adversarial tests;
- regression suites from past failures;
- cross-domain transfer tasks;
- benchmark contamination checks;
- honest accounting of unsolved tasks.

### 7. Independent Verification

The verifier boundary must remain outside the optimization target. A system may
propose verifier changes, but it must not be able to silently adopt them inside
the same run that benefits from them.

Evidence required:

- trusted verifier fingerprints for every run;
- immutable promotion criteria during a run;
- review-only quarantine for proposed verifier or gate changes;
- explicit human approval for trusted-core changes;
- no scoring from self-report alone.

### 8. Sandboxed Execution

Any generated or modified code must execute behind an isolation boundary.

Evidence required:

- container or VM isolation;
- no ambient credentials;
- network disabled by default;
- CPU, memory, process, and wall-clock limits;
- write access limited to run artifacts;
- full capture of logs, filesystem diffs, exit codes, and resource usage.

### 9. Authority Control

Capability gains should not automatically grant broader authority. The system
can become a better improver without being allowed to change its own operating
constraints.

Evidence required:

- human approval for network access, dependency installation, trusted-code
  changes, model training, benchmark changes, and sandbox-policy changes;
- durable approval records;
- ability to replay what was approved and why;
- default denial for authority expansion.

### 10. Evidence of Compounding

The central test is whether later generations become better at producing future
improvements.

Evidence required:

- generation N improvers solve improvement tasks generation 0 could not solve;
- later generations improve faster or more reliably on hidden episodes;
- gains survive independent reruns;
- improvements are not explained only by benchmark memorization or threshold
  relaxation.

## Model-Level Recursion

The hardest unsolved step is model-level or weight-level self-improvement.
Without improving the underlying model or learning system, the project remains
bounded by a fixed model, verifier, and tool ceiling.

This is an unsolved research target, not a declared impossibility. A major
ambition of the project is to create the infrastructure needed to test whether
model-level recursive improvement can be demonstrated safely and credibly.

A future model-level system would need additional controls:

- isolated training pipelines;
- provenance and licensing checks for training data;
- evaluation before and after training;
- capability and safety regression suites;
- rollback mechanisms;
- strict human approval before deployment;
- monitoring for deceptive or reward-hacking behavior.

This repository should not claim model-level recursive self-improvement until
there is measured, independently verified evidence of a system improving the
learning machinery that powers its own future improvements. Producing that kind
of evidence is an explicit long-term research objective.

## Minimal Honest Milestone

The smallest credible milestone beyond current SRSI is:

1. An LLM-backed proposer generates structured edits to untrusted strategy code.
2. Candidate code runs only in a container sandbox.
3. An archive stores multiple improver variants.
4. Meta-evaluation compares improvers over multiple hidden improvement
   episodes.
5. Trusted verifier and gate code remains immutable during the run.
6. Proposed trusted-core changes are emitted only as review artifacts.
7. A final report shows both promoted improvements and rejected failure modes.

That would still not be AGI or ASI. It would, however, be a concrete move from
parameter-level scaffold improvement toward recursively improving the
improvement process itself.

## Claim Standard

Do not describe the project as fully recursive unless it can show all of the
following:

- the improver changes over generations;
- the changed improver is better at producing future improvements;
- the gains generalize to hidden tasks;
- independent verification remains intact;
- generated code is sandboxed;
- authority expansion is human-gated;
- failures and unsolved tasks are reported honestly.

Until then, the accurate description is: bounded, sandboxed, verifier-first
scaffold improvement.
