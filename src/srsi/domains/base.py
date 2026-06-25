"""The contract every research domain implements.

A domain plugs three things into the domain-agnostic engine:

* a *schema* -- the typed knobs of its strategy that the mutator may turn;
* a deliberately weak *seed genome* to start from;
* an *evaluate* method that runs the (untrusted) strategy on one instance and
  then checks the result with the (trusted) verifier, returning an
  :class:`InstanceOutcome`.

Crucially, ``evaluate`` is where claim-vs-verification reconciliation happens.
The strategy is free to claim whatever it likes; the domain consults the
trusted core and reports ``verified`` and ``integrity_ok`` accordingly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from ..engine.evaluation import InstanceOutcome
from ..engine.genome import Genome
from ..engine.sandbox import Budget
from ..engine.schema import ParamSpec


class Domain(ABC):
    name = "abstract"

    @abstractmethod
    def schema(self) -> Dict[str, ParamSpec]:
        ...

    @abstractmethod
    def seed_genome(self) -> Genome:
        ...

    @abstractmethod
    def instance_ids(self) -> List[str]:
        ...

    @abstractmethod
    def evaluate(self, genome: Genome, instance_id: str, budget: Budget) -> InstanceOutcome:
        ...

    @abstractmethod
    def complexity(self, genome: Genome) -> int:
        """A cheap proxy for genome 'size', used for the parsimony penalty."""
