"""The evolvable scaffold representation.

A :class:`Genome` is a small, declarative bundle of strategy parameters plus
lineage metadata. It is the *only* thing the self-improvement loop ever mutates;
the trusted verifiers are never represented here and so can never be touched by
a mutation. ``genome_id`` is a content hash used for the tamper-evident lineage
log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any, Dict, Mapping, Optional


def _canonical(params: Mapping[str, Any]) -> Dict[str, Any]:
    """JSON-ready, order-independent view of params (tuples become lists)."""

    def convert(value: Any) -> Any:
        if isinstance(value, tuple):
            return [convert(v) for v in value]
        return value

    return {key: convert(params[key]) for key in sorted(params)}


@dataclass(frozen=True)
class Genome:
    domain: str
    params: Mapping[str, Any]
    generation: int = 0
    parent_id: Optional[str] = None
    notes: str = ""

    @property
    def genome_id(self) -> str:
        payload = {
            "domain": self.domain,
            "params": _canonical(self.params),
            "generation": self.generation,
            "parent_id": self.parent_id,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode("utf-8")).hexdigest()[:16]

    def child(self, key: str, value: Any, notes: str) -> "Genome":
        next_params = dict(self.params)
        next_params[key] = value
        return Genome(
            domain=self.domain,
            params=next_params,
            generation=self.generation + 1,
            parent_id=self.genome_id,
            notes=notes,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "domain": self.domain,
            "params": _canonical(self.params),
            "generation": self.generation,
            "parent_id": self.parent_id,
            "notes": self.notes,
        }
