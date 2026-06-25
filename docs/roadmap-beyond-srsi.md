# Roadmap Beyond SRSI

SRSI is an integrity-first scaffold-improvement harness whose long-term goal is
a Fully-Recursive Self-Improving system. It is not an AGI or ASI system today,
and it is not a recipe for turning a small benchmark optimizer into one by
adding a few missing features. Its strongest design choice is also its current
ceiling: the strategy scaffold may improve, while the trusted verifiers and
enforcement code remain fixed.

This document records what would be required to push the project toward that
fully-recursive goal, and where the known open research problems begin. These
problems are not treated as impossibility results. They are the research targets
the project ultimately aims to address.
For a stricter definition of what would justify calling a successor "fully
recursive," see
[`fully-recursive-self-improvement.md`](fully-recursive-self-improvement.md).
For the ordered implementation milestones, see
[`../ROADMAP.md`](../ROADMAP.md).

## Current Ceiling

The current harness improves small parameter genomes interpreted by fixed
strategy code. That gives the project useful properties:

- runs are deterministic and auditable;
- candidate behavior is bounded by explicit step budgets;
- correctness is judged by independent trusted verifiers;
- findings carry calibrated evidence labels;
- held-out evaluation and integrity gates catch simple reward hacking.

Those same properties prevent open-ended recursive self-improvement. The system
does not generate executable code, modify its own trusted core, train model
weights, choose its own evaluators, expand its permissions, or act on the world.
That is deliberate.

## Realistic Next Target

The credible next target is not "fully recursively self-improving AGI/ASI." The
credible target is a stronger sandboxed automated-research scaffold:

1. A proposer that can generate useful candidate changes.
2. A real isolation boundary for any generated code.
3. A broader archive of candidate systems rather than a single hill-climbed
   lineage.
4. Larger, hidden, and adversarial benchmark suites.
5. Independent verifiers that remain outside the optimization target.
6. Human-gated promotion for any change that expands authority.

The project should keep its integrity model while making the untrusted scaffold
more capable.

## Capability Roadmap

### 1. Add a Model-Backed Proposer

`LLMProposer` is currently a disabled placeholder. A first upgrade would let a
frozen model propose structured genome edits:

- input: current genome, recent failures, schema, and domain documentation;
- output: typed parameter changes only, not arbitrary source code;
- validation: parse into the existing schema and reject anything malformed;
- replay: record prompts, model id, temperature, outputs, and parsed edits.

This preserves the current safety boundary while replacing exhaustive neighbor
search with a more capable proposal mechanism.

### 2. Move From Hill-Climbing to an Archive

The current loop promotes one best genome and discards the rest. A more serious
self-improvement harness should keep an archive:

- retain diverse high-performing variants;
- sample parents by performance and novelty;
- compare candidates against multiple baselines;
- preserve specialized strategies that are not globally best yet;
- track ancestry across branches, not just a single line.

This would make the search closer to systems such as Darwin Godel Machine and
ADAS, while still requiring independent evaluation before promotion.

### 3. Add Code-Evolving Candidates Only Behind a Sandbox

The current `sandbox.require_pure` boundary is correct: generated code should
not run in-process. If the project ever allows code-emitting candidates, it
needs a real sandbox first:

- container or VM isolation;
- no ambient credentials;
- network disabled by default;
- strict CPU, memory, process, and wall-clock limits;
- read-only project inputs and write-only artifact directories;
- syscall or capability restrictions where available;
- deterministic dependency snapshots;
- complete capture of stdout, stderr, files, exit codes, and resource usage.

Generated code should be treated as hostile until it passes structure, runtime,
behavioral, and integrity checks.

### 4. Expand Benchmarks and Verifiers

The current domains are intentionally small. A more capable system would need
many more tasks and stronger evaluators:

- public smoke tests for development;
- private held-out tests for promotion;
- rotating adversarial tests;
- contamination checks;
- regression suites from past failures;
- long-horizon tasks with delayed feedback;
- cross-domain tasks that require tool use and research planning.

The system should optimize on a selection set but only promote on independent
held-out evidence. It should never be allowed to write, select, or relax the
promotion evaluator for itself.

### 5. Preserve Independent Verification

The verifier boundary is non-negotiable. Any future system should maintain a
hard distinction between:

- the untrusted proposer or candidate;
- the sandbox that executes it;
- the benchmark harness that measures it;
- the trusted verifier that assigns evidence;
- the human or policy gate that expands permissions.

A candidate may propose changes to trusted code, but such changes should be
quarantined as review artifacts. They should not take effect inside the same
run that proposed them.

### 6. Add Human-Gated Authority Expansion

Capability and authority should be separated. Even if a candidate performs
better, that should not automatically grant it broader access. Require explicit
human approval for changes that:

- alter trusted verifiers or gates;
- modify sandbox policy;
- enable network access;
- access secrets or credentials;
- install dependencies;
- write outside run artifacts;
- schedule future actions;
- train or fine-tune models;
- change benchmark selection or thresholds.

The system may earn promotion as a better solver without earning more authority.

## Open Research Blockers to Fully Recursive AGI/ASI

Several obstacles are not solved by this repository and are not solved in the
field. That absence of a demonstration does not imply impossibility; it defines
the research frontier this project is meant to approach:

- no verified demonstration yet of open-ended weight-level recursive
  self-improvement;
- no reliable automated evaluator for most long-horizon AI research;
- no general solution to reward hacking under self-modification;
- no proven method for safely letting a system modify its own oversight;
- no assurance that scaffold improvements exceed the fixed base model's
  capability ceiling;
- no settled alignment or control framework for autonomous AI R&D.

Because of these blockers, SRSI should not claim that fully functional AGI/ASI
or open-ended model-level recursive self-improvement has already been achieved.
The project aim is stronger: build a research platform capable of producing
credible AGI/ASI-relevant breakthroughs that test whether these blockers can be
overcome under independent verification, sandboxing, and human-gated authority
control.

## Practical Milestones

Useful milestones, in increasing risk order:

1. Add replayable LLM-backed structured genome proposals.
2. Add archive search and novelty tracking.
3. Add larger held-out and adversarial benchmark suites.
4. Add signed or hash-pinned benchmark and verifier manifests.
5. Add a container sandbox for code-emitting candidates.
6. Add candidate-generated code patches as review-only artifacts.
7. Add human-approved promotion of reviewed patches into untrusted strategy
   code.
8. Add external red-team suites and benchmark contamination checks.
9. Add policy-gated limited network/tool use inside sandboxes.
10. Add long-horizon research tasks with auditable intermediate artifacts.

Each milestone should come with tests that demonstrate both successful
improvement and failed attempts being contained.

## Definition of Done for a Stronger Harness

A stronger successor to SRSI should be able to show:

- measurable improvement over seed systems on hidden held-out tasks;
- no promotion from unverified self-report;
- reproducible lineage and candidate artifacts;
- sandbox containment for failing or malicious candidates;
- independent verifier fingerprints for every run;
- explicit evidence labels for every finding;
- honest accounting of unsolved tasks;
- human approval records for every authority expansion.

That would be a serious automated-research harness. It would still not, by
itself, be fully recursively self-improving AGI/ASI.
