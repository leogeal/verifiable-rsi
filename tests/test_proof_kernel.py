from srsi.trusted.proof_kernel import (
    EMPTY_CLAUSE,
    ProofStep,
    Refutation,
    is_tautology_clause,
    is_unsat,
    resolve,
    verify_refutation,
)


def c(*lits):
    return frozenset(lits)


def test_resolve_basic():
    assert resolve(c(1, 2), c(-1, 3), 1) == c(2, 3)


def test_resolve_to_empty():
    assert resolve(c(1), c(-1), 1) == EMPTY_CLAUSE


def test_resolve_requires_complementary_pivot():
    assert resolve(c(1, 2), c(3), 1) is None


def test_tautology_detection():
    assert is_tautology_clause(c(1, -1))
    assert not is_tautology_clause(c(1, 2))


def test_verify_accepts_valid_refutation():
    inputs = [c(1), c(-1)]
    proof = Refutation((ProofStep(0, 1, 1),))
    verdict = verify_refutation(inputs, proof)
    assert verdict.ok


def test_verify_rejects_invalid_step():
    # 1 is not resolvable between {2} and {3}
    inputs = [c(2), c(3)]
    proof = Refutation((ProofStep(0, 1, 1),))
    assert not verify_refutation(inputs, proof).ok


def test_verify_rejects_when_empty_never_reached():
    inputs = [c(1, 2), c(-1, 3)]
    proof = Refutation((ProofStep(0, 1, 1),))  # derives {2,3}, not empty
    verdict = verify_refutation(inputs, proof)
    assert not verdict.ok


def test_verify_rejects_out_of_range_index():
    inputs = [c(1), c(-1)]
    proof = Refutation((ProofStep(0, 5, 1),))
    assert not verify_refutation(inputs, proof).ok


def test_is_unsat_oracle():
    assert is_unsat([c(1), c(-1)])
    assert not is_unsat([c(1, 2)])  # satisfiable
    # All full-length clauses over two variables are jointly unsatisfiable.
    all2 = [c(1, 2), c(1, -2), c(-1, 2), c(-1, -2)]
    assert is_unsat(all2)
