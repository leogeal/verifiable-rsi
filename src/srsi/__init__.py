"""SRSI -- Sandboxed Recursive Self-Improvement.

An integrity-first, self-improving research harness. A deterministic search
loop evolves *strategy genomes* (the scaffold) while a small, immutable trusted
core verifies every result. The loop can prove propositional theorems, discover
closed forms for integer sequences, and rediscover conserved quantities in
mechanical systems -- and it reports each finding only at the evidence level its
verifier can actually justify, while naming the things it could not establish.

This is the honest, buildable version of "recursive self-improvement": the
scaffold improves over a fixed verifier ceiling, exactly as the accompanying
research report (rsi-research-report.md) describes for the published systems.
"""

from __future__ import annotations

__version__ = "0.1.0"


def available_domains():
    return ("theorem", "math", "physics")


def build_domain(name: str):
    """Instantiate a research domain by name (lazy import avoids cycles)."""

    if name == "theorem":
        from .domains.theorem import TheoremDomain

        return TheoremDomain()
    if name == "math":
        from .domains.math_research import MathResearchDomain

        return MathResearchDomain()
    if name == "physics":
        from .domains.physics import PhysicsDomain

        return PhysicsDomain()
    raise ValueError(
        "unknown domain {!r}; choose from {}".format(name, ", ".join(available_domains()))
    )
