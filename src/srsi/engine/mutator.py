"""Proposers that generate candidate genomes from the current one.

The default :class:`DeterministicProposer` enumerates every one-step neighbour
allowed by the schema -- change exactly one parameter to one adjacent value.
This makes the search reproducible and auditable, and it is the honest analogue
of the LLM-driven mutator described in the research report: same loop shape, with
a deterministic proposer standing in for a frozen model so the harness runs
offline and every run is replayable.

:class:`LLMProposer` documents where a frozen frontier model would plug in. It
is intentionally inert by default -- constructing it without an explicit client
raises -- so no network call or nondeterminism sneaks into a default run.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from .genome import Genome
from .schema import ParamSpec


@dataclass(frozen=True)
class Candidate:
    genome: Genome
    changed_key: str
    changed_value: Any


class Proposer(ABC):
    @abstractmethod
    def propose(self, genome: Genome) -> List[Candidate]:
        ...


class DeterministicProposer(Proposer):
    def __init__(self, schema: Dict[str, ParamSpec]):
        self.schema = schema

    def propose(self, genome: Genome) -> List[Candidate]:
        out: List[Candidate] = []
        for key in sorted(self.schema):
            spec = self.schema[key]
            current = genome.params.get(key)
            for value in spec.neighbors(current):
                child = genome.child(key, value, "set {}={}".format(key, value))
                out.append(Candidate(child, key, value))
        return out


class LLMProposer(Proposer):
    """Placeholder for a frozen-model-driven scaffold mutator.

    A real implementation would feed the current genome plus recent failure
    transcripts to a frozen frontier model and parse structured edits back into
    genomes. It stays disabled by default: the default harness is deterministic
    and offline, and enabling a model proposer is an explicit, separate choice.
    """

    def __init__(self, client: Any = None):
        if client is None:
            raise RuntimeError(
                "LLMProposer requires an explicit model client; the default "
                "harness uses DeterministicProposer for reproducible, offline runs"
            )
        self.client = client

    def propose(self, genome: Genome) -> List[Candidate]:  # pragma: no cover
        raise NotImplementedError("wire in a frozen-model client to enable LLM proposals")
