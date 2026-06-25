"""Typed parameter specifications for the evolvable genome.

A domain describes the knobs of its strategy with these specs. The mutator asks
each spec for the deterministic set of one-step neighbours of the current value,
so the whole search is reproducible and stays inside declared bounds -- a
candidate can never reference an option the schema does not allow. Subsets and
pairs are encoded as tuples inside a :class:`Categorical`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple


class ParamSpec:
    def neighbors(self, value: Any) -> List[Any]:
        raise NotImplementedError

    def is_valid(self, value: Any) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class IntRange(ParamSpec):
    lo: int
    hi: int
    step: int = 1

    def neighbors(self, value: Any) -> List[Any]:
        out = []
        for delta in (-self.step, self.step):
            candidate = value + delta
            if self.lo <= candidate <= self.hi:
                out.append(candidate)
        return out

    def is_valid(self, value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and self.lo <= value <= self.hi


@dataclass(frozen=True)
class Toggle(ParamSpec):
    def neighbors(self, value: Any) -> List[Any]:
        return [not value]

    def is_valid(self, value: Any) -> bool:
        return isinstance(value, bool)


@dataclass(frozen=True)
class Categorical(ParamSpec):
    options: Tuple[Any, ...]

    def neighbors(self, value: Any) -> List[Any]:
        return [opt for opt in self.options if opt != value]

    def is_valid(self, value: Any) -> bool:
        return value in self.options


@dataclass(frozen=True)
class RealChoice(ParamSpec):
    options: Tuple[float, ...]  # ascending

    def neighbors(self, value: Any) -> List[Any]:
        opts = list(self.options)
        if value in opts:
            i = opts.index(value)
            out = []
            if i > 0:
                out.append(opts[i - 1])
            if i < len(opts) - 1:
                out.append(opts[i + 1])
            return out
        return list(opts)

    def is_valid(self, value: Any) -> bool:
        return value in self.options
