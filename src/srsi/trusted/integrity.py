"""Integrity primitives shared by every trusted verifier.

This module is part of the TRUSTED CORE. The self-improvement loop is never
allowed to modify anything under ``srsi/trusted``; ``trusted_fingerprint`` lets
the engine prove that nothing did.

The central honesty mechanism is the :class:`Evidence` ladder. A result may
only carry the evidence level its *verification* actually justifies. The engine
calls :func:`assert_supported` so that a strategy can never label an unproven
conjecture as ``PROVED`` -- if it tries, the run aborts with an
:class:`OverclaimError` and the offending candidate is quarantined.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, List


class Evidence(IntEnum):
    """How strongly a claim is supported, from weakest to strongest.

    The ordering is meaningful: ``REFUTED < CONJECTURE < EMPIRICAL <
    VERIFIED_SYMBOLIC < PROVED``. A claim's evidence may never exceed the
    ceiling that its verifier returns.
    """

    REFUTED = 0            # an oracle showed the claim is false
    CONJECTURE = 1         # proposed; no independent verification yet
    EMPIRICAL = 2          # holds on held-out instances; no proof (e.g. physics)
    VERIFIED_SYMBOLIC = 3  # exact symbolic / dimensional verification
    PROVED = 4             # machine-checked proof by the trusted kernel


EVIDENCE_LABEL = {
    Evidence.REFUTED: "refuted",
    Evidence.CONJECTURE: "conjecture",
    Evidence.EMPIRICAL: "empirical",
    Evidence.VERIFIED_SYMBOLIC: "verified-symbolic",
    Evidence.PROVED: "proved",
}


class IntegrityError(RuntimeError):
    """Base class for any violation of the harness's honesty guarantees."""


class OverclaimError(IntegrityError):
    """Raised when a result claims more evidence than its verifier supports."""


class TamperError(IntegrityError):
    """Raised when the trusted verifier core changed during a run."""


@dataclass(frozen=True)
class Claim:
    """A single, evidence-labelled research output.

    ``support`` records the quantitative backing (e.g. the number of held-out
    instances a physics invariant survived, or the degree bound at which a
    polynomial identity was checked). ``verified`` is set by the trusted
    verifier and is the *only* authority on whether the claim is sound.
    """

    statement: str
    evidence: Evidence
    detail: str = ""
    support: int = 0
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statement": self.statement,
            "evidence": int(self.evidence),
            "evidence_label": EVIDENCE_LABEL[self.evidence],
            "detail": self.detail,
            "support": self.support,
            "verified": self.verified,
        }


def assert_supported(claim: Claim, ceiling: Evidence) -> None:
    """Abort if ``claim`` asserts stronger evidence than ``ceiling`` allows.

    ``ceiling`` is computed by the trusted verifier from what it could actually
    confirm. This is the structural guard against the failure mode the research
    report documents (DGM faking test logs): a candidate cannot promote an
    unverified result to ``PROVED`` because this check sits between it and the
    audit log.
    """

    if claim.evidence > ceiling:
        raise OverclaimError(
            "result claims evidence {!r} but verification only supports {!r}: {}".format(
                EVIDENCE_LABEL[claim.evidence], EVIDENCE_LABEL[ceiling], claim.statement
            )
        )


def fingerprint_files(paths: Iterable[Path]) -> str:
    """Return a stable SHA-256 over the names and contents of ``paths``."""

    digest = sha256()
    for path in sorted(paths, key=lambda p: p.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def trusted_dir() -> Path:
    """Filesystem location of the trusted verifier package."""

    return Path(__file__).resolve().parent


def trusted_fingerprint() -> str:
    """Fingerprint every ``.py`` file in the trusted verifier core."""

    files: List[Path] = sorted(trusted_dir().glob("*.py"))
    return fingerprint_files(files)


# The honesty contract depends on more than the verifier primitives: it also
# depends on the enforcement layer that *calls* them -- the code that derives
# accuracy from ``verified`` (not ``claimed``), rejects integrity violations,
# and drives the loop. These engine modules are therefore protected too.
_PROTECTED_ENGINE = ("evaluation.py", "gates.py", "improver.py")


def protected_fingerprint() -> str:
    """Fingerprint the full integrity-critical surface: the trusted verifier
    core plus the honesty-enforcing engine modules.

    Keyed by *relative path* (not bare filename) so coverage stays correct even
    if a subpackage is later added. The engine records this once at the start of
    a run and re-checks it before every generation and again before publishing
    findings; any change aborts the run.
    """

    base = trusted_dir()
    engine = base.parent / "engine"
    labelled: List[tuple] = [("trusted/" + p.name, p) for p in base.glob("*.py")]
    labelled += [("engine/" + name, engine / name) for name in _PROTECTED_ENGINE]

    digest = sha256()
    for rel, path in sorted(labelled, key=lambda item: item[0]):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
