# SRSI — Sandboxed Recursive Self-Improvement

An **integrity-first, self-improving research harness**. A deterministic search
loop improves a *strategy* (the scaffold) over a *fixed, immutable verifier*
(the ceiling), and can:

- **prove propositional theorems** (resolution refutations, machine-checked),
- **discover closed forms** for integer sequences (exact symbolic verification),
- **rediscover conserved quantities** in mechanical systems (empirical, on
  held-out trajectories).

It is the honest, buildable version of "recursive self-improvement." It is **not**
an AGI, and it makes no attempt to modify its own model weights, escape its
process, or remove its own oversight. Those properties are deliberate, and the
companion report [`rsi-research-report.md`](rsi-research-report.md) explains why
they are exactly where every *real* self-improving system to date also stops:
the scaffold improves, the verifier is the ceiling.

## Project goal

The long-term goal of this project is a **Fully-Recursive Self-Improving
system**: a system that can safely improve not only task-level strategies, but
also the machinery that proposes, tests, verifies, and promotes future
improvements.

The current codebase is an integrity-first stepping stone toward that goal. It
deliberately starts with bounded scaffold improvement, fixed trusted verifiers,
held-out evaluation, and auditable lineage before attempting more recursive
capabilities. The criteria for honestly claiming fully-recursive
self-improvement are documented in
[`docs/fully-recursive-self-improvement.md`](docs/fully-recursive-self-improvement.md).

The fact that open-ended model-level or weight-level recursive
self-improvement has not yet been demonstrated is treated here as a research
frontier, not as evidence that it cannot be done. The project's ambition is to
support AGI/ASI-relevant research breakthroughs that test, and eventually may
demonstrate, whether fully-recursive self-improvement can be made to work under
independent verification and explicit control boundaries.

## Why this design is honest

The single most important property: **the thing that judges correctness is never
the thing that gets to improve.**

```
            mutated, untrusted                 fixed, trusted (de Bruijn core)
        ┌────────────────────────┐         ┌────────────────────────────────┐
        │  strategy genome        │ propose │  proof kernel (resolution)      │
        │  (search heuristics)    │────────▶│  symbolic identity checker      │
        │                         │ result  │  dimensional analysis           │
        │  proposes results       │◀────────│  held-out evaluation            │
        └────────────────────────┘ verify   └────────────────────────────────┘
                 srsi/strategies                        srsi/trusted
```

Concretely, the harness defends honesty four ways:

1. **Verification is independent of the optimiser.** A strategy may *claim*
   anything; a result only counts if the trusted core re-derives it. Accuracy is
   computed from `verified`, never from `claimed`. Verifier thresholds (e.g. the
   physics held-out constancy tolerance) are fixed trusted constants, never
   genome parameters — the thing being judged never sets its own passing bar.
2. **Calibrated evidence levels.** Every finding is labelled with the strongest
   evidence its verifier supports — `PROVED` (kernel), `VERIFIED_SYMBOLIC`
   (exact identity), or `EMPIRICAL` (held-out numerical) — and a result can never
   be promoted above that ceiling (`assert_supported`).
3. **Held-out evaluation.** Search progresses on a *selection* set; promotion
   requires the *held-out* set not to regress. A formula that fits its fitted
   terms but fails the held-out terms of the same instance is never reported as
   solved.
4. **Tamper-evidence.** The integrity-critical core — the trusted verifiers
   *and* the honesty-enforcing engine modules (`gates`, `evaluation`,
   `improver`) — is fingerprinted (SHA-256) at the start of every run, re-checked
   before every generation, and re-checked once more before findings are
   published; any change aborts the run. The audit log is a hash chain
   (`verify`), so a record cannot be edited after the fact.

And it reports what it could **not** do: every run lists its *honestly unsolved*
instances, so absence of a finding is visible, never hidden. The theorem domain
even ships a deliberate temptation — a `trust_self_report` flag that makes the
strategy claim proofs it never completed — purely to demonstrate the integrity
gate catching it (this is the DGM "faked the test logs" failure mode, contained).

## Quick start

```bash
# Prove propositional theorems; self-improve the proof-search heuristic.
PYTHONPATH=src python3 -m srsi.cli run --domain theorem --out runs/theorem

# Discover closed forms for integer sequences.
PYTHONPATH=src python3 -m srsi.cli run --domain math --seed 5 --out runs/math

# Rediscover conserved quantities from trajectories.
PYTHONPATH=src python3 -m srsi.cli run --domain physics --seed 5 --out runs/physics

# Re-check a finished run's audit trail (lineage hash chain + trusted fingerprint).
PYTHONPATH=src python3 -m srsi.cli verify runs/theorem

# List domains; run the tests.
PYTHONPATH=src python3 -m srsi.cli list-domains
python3 -m pytest
```

(The `--seed` flags on math/physics just pick a selection/held-out split whose
*training* set spans the full difficulty range, so the climb has signal at every
rung; any seed is valid, it only changes which instances are held out.)

## What a run shows

- **theorem** — climbs from a weak seed (tight clause-length cap, no heuristic)
  to proving all benchmark instances; reports 7 `PROVED` findings and catches the
  `trust_self_report` cheat as an integrity violation.
- **math** — climbs polynomial degree 0→4, discovers all nine polynomial closed
  forms as `VERIFIED_SYMBOLIC` (e.g. `sum_cubes: a(n)=¼n²+½n³+¼n⁴`), and honestly
  lists the three non-polynomial sequences (`pow2`, `fibonacci`, `factorial`) as
  unsolved.
- **physics** — discovers `x² + (m/k)·v²` for oscillators and `v² + 2g·h` for
  free-fall, all `EMPIRICAL`, verified constant on held-out trajectories, with
  correct physical dimensions.

## Architecture

```
src/srsi/
  trusted/            # IMMUTABLE verifier core — never mutated by the loop
    integrity.py        # Evidence ladder, overclaim guard, tamper fingerprint
    proof_kernel.py     # sound resolution checker + brute-force UNSAT oracle
    symbolic.py         # exact rational polynomial-identity verification
    dimensions.py       # SI dimensional analysis
    holdout.py          # deterministic selection/held-out split
  strategies/         # EVOLVABLE scaffold — untrusted, mutable
    proof_search.py     # heuristic resolution search (genome-tuned)
    formula_search.py   # polynomial closed-form search
    invariant_search.py # conserved-quantity (least-variance) search
  domains/            # wire a strategy to a verifier; reconcile claim vs. verified
    theorem.py · math_research.py · physics.py
  engine/             # domain-agnostic loop
    genome.py · schema.py · mutator.py · gates.py · sandbox.py · lineage.py · improver.py
  cli.py
```

## How this maps to the research report

The report finds that every verified self-improving system (Darwin Gödel
Machine, STOP, ADAS, Voyager, AlphaEvolve) improves only its **scaffold** over a
**frozen** model, and that the original Gödel machine's *provable-benefit*
requirement was abandoned as impractical. SRSI is a small, honest instance of
exactly that shape:

- The **trusted proof kernel / verifiers** play the role of the frozen ceiling.
  The loop's gains plateau at what they can verify within budget — observed
  directly when each domain converges.
- The **strategy genome** is the scaffold that actually improves.
- Unlike the original Gödel machine, promotion is by **empirical benchmark
  validation**, not proof of net benefit — the same concession the field made.
- The harness uses a **deterministic proposer** by default so runs are
  reproducible and offline; `engine/mutator.py:LLMProposer` documents where a
  frozen frontier model would plug in (disabled by default).

## Roadmap beyond this prototype

The project can be extended toward a stronger sandboxed automated-research
scaffold, but not by simply flipping a switch into AGI/ASI. The next credible
steps are model-backed structured proposals, archive search, larger held-out
benchmarks, and a real OS-level sandbox before any generated code is executed.
See [`docs/roadmap-beyond-srsi.md`](docs/roadmap-beyond-srsi.md) and
[`docs/fully-recursive-self-improvement.md`](docs/fully-recursive-self-improvement.md).
The actionable milestone plan is in
[`ROADMAP.md`](ROADMAP.md).

## Scope and boundaries (by design)

- **No weight-level self-improvement.** The model/verifier is fixed; only the
  scaffold changes. This is the field's actual frontier, not a limitation we
  could lift with a flag.
- **No code generation, no sandbox escape.** Strategies are *parameter genomes
  interpreted by fixed code*, bounded by a step budget — there is no `exec` and
  nothing to escape. `engine/sandbox.py:require_pure` refuses to run
  generated code in-process; a code-emitting proposer would require a real
  OS-level sandbox first.
- **Human-in-the-loop by construction.** The loop runs a fixed number of
  generations and writes an auditable trail; it does not act on the world.
