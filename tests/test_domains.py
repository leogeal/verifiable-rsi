"""Domain-level tests: the claim-vs-verification reconciliation that makes the
harness honest, exercised directly without the search loop."""

from srsi.domains.math_research import MathResearchDomain
from srsi.domains.physics import PhysicsDomain
from srsi.domains.theorem import TheoremDomain
from srsi.engine.genome import Genome
from srsi.engine.sandbox import Budget
from srsi.trusted.integrity import Evidence


def _budget():
    return Budget(400)


# --- theorem -------------------------------------------------------------

def _theorem_genome(**overrides):
    params = {
        "w_len": 1.0,
        "w_age": 0.0,
        "max_len": 6,
        "use_sos": False,
        "trust_self_report": False,
    }
    params.update(overrides)
    return Genome("theorem", params)


def test_theorem_proves_and_kernel_verifies():
    domain = TheoremDomain()
    outcome = domain.evaluate(_theorem_genome(), "all3", _budget())
    assert outcome.verified
    assert outcome.evidence == Evidence.PROVED
    assert outcome.integrity_ok
    assert outcome.claim is not None and outcome.claim.evidence == Evidence.PROVED


def test_theorem_honest_failure_makes_no_claim():
    # Tight clause-length cap and no cheating: the strategy gives up honestly.
    domain = TheoremDomain()
    outcome = domain.evaluate(_theorem_genome(max_len=2), "all4", _budget())
    assert not outcome.verified
    assert not outcome.claimed
    assert outcome.integrity_ok
    assert outcome.claim is None


def test_theorem_integrity_violation_is_caught():
    # The cheat flag makes the strategy claim success it cannot back up.
    domain = TheoremDomain()
    outcome = domain.evaluate(_theorem_genome(max_len=2, trust_self_report=True), "all4", _budget())
    assert outcome.claimed
    assert not outcome.verified
    assert not outcome.integrity_ok  # the kernel caught the bogus claim


# --- math ----------------------------------------------------------------

def test_math_verifies_polynomial_symbolically():
    domain = MathResearchDomain()
    genome = Genome("math", {"max_degree": 2, "parsimony": True})
    outcome = domain.evaluate(genome, "squares", _budget())
    assert outcome.verified
    assert outcome.evidence == Evidence.VERIFIED_SYMBOLIC


def test_math_solves_quartic_with_enough_degree():
    domain = MathResearchDomain()
    genome = Genome("math", {"max_degree": 4, "parsimony": True})
    outcome = domain.evaluate(genome, "sum_cubes", _budget())
    assert outcome.verified
    assert outcome.evidence == Evidence.VERIFIED_SYMBOLIC


def test_math_does_not_fabricate_for_nonpolynomial():
    domain = MathResearchDomain()
    genome = Genome("math", {"max_degree": 6, "parsimony": True})
    for seq in ("pow2", "fibonacci", "factorial"):
        outcome = domain.evaluate(genome, seq, _budget())
        assert not outcome.verified, seq
        assert outcome.claim is None, seq


# --- physics -------------------------------------------------------------

def test_physics_finds_conserved_quantity():
    domain = PhysicsDomain()
    genome = Genome("physics", {"candidate_features": ("x2", "v2", "h")})
    for system in domain.instance_ids():
        outcome = domain.evaluate(genome, system, _budget())
        assert outcome.verified, system
        assert outcome.evidence == Evidence.EMPIRICAL, system


def test_physics_rejects_wrong_features():
    domain = PhysicsDomain()
    genome = Genome("physics", {"candidate_features": ("x", "v", "h")})
    outcome = domain.evaluate(genome, "oscillator_unit", _budget())
    assert not outcome.verified


def test_physics_reports_coefficient_dimension():
    # The dimensional structure is reported honestly: oscillator energy x^2 + c*v^2
    # needs a dimensionful coefficient (c ~ time^2), so the claim must say so.
    domain = PhysicsDomain()
    genome = Genome("physics", {"candidate_features": ("x2", "v2", "h")})
    outcome = domain.evaluate(genome, "oscillator_unit", _budget())
    assert outcome.verified
    assert "coefficient dimension" in outcome.claim.statement
