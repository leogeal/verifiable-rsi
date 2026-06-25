"""Bounded execution for strategies.

The harness self-improves *parameter genomes interpreted by fixed code*, never
arbitrary generated source, so there is no ``exec``/``eval`` and nothing to
escape: execution is bounded by construction. The remaining resource to bound is
compute, which :class:`Budget` does -- every strategy ticks the budget in its
search loops and is cut off deterministically when it is spent. This makes a
slow or non-terminating strategy a *measured failure* rather than a hang.

If a future proposer is ever allowed to emit executable code (the next rung on
the ladder described in the research report), this is where an OS-level sandbox
backend would have to be required before any such code runs. ``require_pure``
documents and enforces that boundary today.
"""

from __future__ import annotations

from dataclasses import dataclass


class BudgetExceeded(RuntimeError):
    """Raised when a strategy exhausts its step budget."""


@dataclass
class Budget:
    max_steps: int
    used: int = 0

    def tick(self, n: int = 1) -> None:
        self.used += n
        if self.used > self.max_steps:
            raise BudgetExceeded("step budget {} exceeded".format(self.max_steps))

    def remaining(self) -> int:
        return max(0, self.max_steps - self.used)


def require_pure(emits_code: bool) -> None:
    """Guard the boundary between parameter-search and code-generation.

    The default harness only ever interprets genomes, so ``emits_code`` is
    ``False`` everywhere today. If a code-emitting proposer is wired in without
    an OS-level sandbox, this raises rather than silently running untrusted code.
    """

    if emits_code:
        raise RuntimeError(
            "code-emitting proposers require an explicit OS-level sandbox backend; "
            "refusing to execute generated code in-process"
        )
