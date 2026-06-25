"""End-to-end tests of the recursive self-improvement loop."""

import pytest

from srsi import build_domain
from srsi.engine import improver as improver_module
from srsi.engine.improver import RecursiveImprover
from srsi.engine.lineage import verify_chain


def _run(domain_name, **kw):
    iterations = kw.pop("iterations", 14)
    budget = kw.pop("budget", 250)
    domain = build_domain(domain_name)
    improver = RecursiveImprover(domain, budget_steps=budget, **kw)
    seed_sel, _ = improver._evaluate_set(domain.seed_genome(), improver.selection_ids)
    result = improver.run(iterations=iterations)
    return improver, seed_sel, result


def test_theorem_run_improves_and_is_honest():
    improver, seed_sel, result = _run("theorem")
    # The loop made progress over the deliberately weak seed.
    assert result.counters["promotions"] >= 1
    assert result.best_selection.accuracy > seed_sel.accuracy
    # Every reported finding is kernel-proved; nothing weaker sneaks in.
    assert result.findings
    assert all(f["evidence_label"] == "proved" for f in result.findings)
    # Honesty accounting: every instance is either a verified finding or named unsolved.
    total = len(improver.selection_ids) + len(improver.holdout_ids)
    assert len(result.findings) + len(result.unsolved) == total
    # No integrity violation ever survives into the promoted lineage.
    assert result.best_selection.integrity_violations == 0


def test_lineage_chain_is_intact():
    _, _, result = _run("theorem")
    records = [r.to_dict() for r in result.records]
    assert verify_chain(records)


def test_lineage_tamper_is_detected():
    _, _, result = _run("theorem")
    records = [r.to_dict() for r in result.records]
    assert records  # there is something to tamper with
    records[0]["accepted"] = not records[0]["accepted"]
    assert not verify_chain(records)


def test_math_run_yields_symbolic_findings():
    improver, seed_sel, result = _run("math", iterations=16)
    assert result.best_selection.accuracy > seed_sel.accuracy
    labels = {f["evidence_label"] for f in result.findings}
    assert "verified-symbolic" in labels
    # The non-polynomial sequences are honestly reported as unsolved.
    for seq in ("pow2", "fibonacci", "factorial"):
        assert seq in result.unsolved


def test_physics_run_finds_empirical_invariants():
    improver, seed_sel, result = _run("physics", iterations=10)
    assert result.best_selection.accuracy > seed_sel.accuracy
    assert result.findings
    assert all(f["evidence_label"] == "empirical" for f in result.findings)


def test_tamper_with_trusted_core_aborts_run(monkeypatch):
    # If the trusted verifier fingerprint changes mid-run, the loop must abort
    # rather than keep trusting a mutated verifier.
    domain = build_domain("theorem")
    improver = RecursiveImprover(domain, budget_steps=120)
    calls = {"n": 0}

    def fake_fingerprint():
        calls["n"] += 1
        return "baseline" if calls["n"] == 1 else "tampered"

    monkeypatch.setattr(improver_module, "protected_fingerprint", fake_fingerprint)
    with pytest.raises(improver_module.TamperError):
        improver.run(iterations=3)


def test_integrity_gate_blocks_cheating_candidates():
    # Across a full run the proposer will try the trust_self_report cheat; the
    # integrity gate must reject every such candidate (never promote one).
    improver, _, result = _run("theorem")
    assert result.counters["rejected_integrity"] >= 1
    # The promoted strategy never has the cheat enabled.
    assert result.best_genome.params["trust_self_report"] is False
