"""A small, sound proof kernel for propositional logic.

This is the integrity anchor for the theorem-proving domain. It does two jobs,
both deliberately simple enough to audit by eye:

* :func:`verify_refutation` -- the *checker*. Given a set of input clauses and a
  candidate resolution proof, it independently re-derives every resolvent and
  reports whether the empty clause is reached. A strategy cannot smuggle in an
  unjustified clause: the kernel only ever recomputes resolvents from premises
  it was given. This is the de Bruijn criterion -- trust reduces to this file.

* :func:`is_unsat` -- a brute-force *oracle* used only to build benchmarks and
  to independently confirm a problem's true status (so a strategy that claims a
  refutation of a *satisfiable* formula is caught as an integrity violation).

Literals are non-zero integers; ``-x`` is the negation of ``x``. A clause is a
``frozenset`` of literals (a disjunction). The empty clause is unsatisfiable.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import FrozenSet, List, Optional, Sequence, Set, Tuple

Literal = int
Clause = FrozenSet[int]
EMPTY_CLAUSE: Clause = frozenset()


def is_tautology_clause(clause: Clause) -> bool:
    """True if the clause contains a literal and its negation (always true)."""

    return any(-lit in clause for lit in clause)


def resolve(c1: Clause, c2: Clause, pivot: Literal) -> Optional[Clause]:
    """Resolve ``c1`` and ``c2`` on ``pivot``.

    Requires ``pivot in c1`` and ``-pivot in c2``. Returns the resolvent, or
    ``None`` if the pivot does not occur with the required polarities. The
    resolvent drops both pivot literals and unions the rest.
    """

    if pivot not in c1 or -pivot not in c2:
        return None
    resolvent = (set(c1) - {pivot}) | (set(c2) - {-pivot})
    return frozenset(resolvent)


@dataclass(frozen=True)
class ProofStep:
    """Resolve the clauses currently at indices ``i`` and ``j`` on ``pivot``.

    Indices refer to a growing list that starts as the input clauses; each step
    appends its resolvent, so later steps may reference earlier resolvents. This
    ordering must match between the searcher that emits steps and the kernel
    that replays them.
    """

    i: int
    j: int
    pivot: Literal


@dataclass(frozen=True)
class Refutation:
    steps: Tuple[ProofStep, ...]


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str


def verify_refutation(inputs: Sequence[Clause], proof: Refutation) -> Verdict:
    """Independently check that ``proof`` refutes ``inputs``.

    Returns ``ok=True`` only if every step is a valid resolution of two earlier
    clauses and the empty clause appears in the derivation. The kernel trusts
    nothing in ``proof`` except the indices and pivots: it recomputes each
    resolvent itself.
    """

    clauses: List[Clause] = list(inputs)
    for step_no, step in enumerate(proof.steps):
        size = len(clauses)
        if not (0 <= step.i < size and 0 <= step.j < size):
            return Verdict(False, "step {}: clause index out of range".format(step_no))
        resolvent = resolve(clauses[step.i], clauses[step.j], step.pivot)
        if resolvent is None:
            return Verdict(
                False,
                "step {}: {} and {} do not resolve on pivot {}".format(
                    step_no, set(clauses[step.i]), set(clauses[step.j]), step.pivot
                ),
            )
        clauses.append(resolvent)

    if any(c == EMPTY_CLAUSE for c in clauses):
        return Verdict(True, "empty clause derived in {} steps".format(len(proof.steps)))
    return Verdict(False, "derivation valid but empty clause never reached")


def variables_of(clauses: Sequence[Clause]) -> List[int]:
    seen: Set[int] = set()
    for clause in clauses:
        for lit in clause:
            seen.add(abs(lit))
    return sorted(seen)


def is_unsat(clauses: Sequence[Clause], max_vars: int = 22) -> bool:
    """Brute-force unsatisfiability oracle for small formulas.

    Enumerates every assignment over the variables that occur. Returns ``True``
    iff no assignment satisfies all clauses. Refuses formulas with more than
    ``max_vars`` variables so the oracle stays fast and total -- benchmarks are
    built well within this bound.
    """

    variables = variables_of(clauses)
    if len(variables) > max_vars:
        raise ValueError(
            "is_unsat refuses {} variables (> {}); keep benchmark instances small".format(
                len(variables), max_vars
            )
        )
    if any(c == EMPTY_CLAUSE for c in clauses):
        return True
    for bits in product((False, True), repeat=len(variables)):
        assignment = {var: val for var, val in zip(variables, bits)}
        satisfied = True
        for clause in clauses:
            if not any(
                (assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)])
                for lit in clause
            ):
                satisfied = False
                break
        if satisfied:
            return False
    return True
