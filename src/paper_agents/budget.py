from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from time import monotonic


class BudgetExceeded(RuntimeError):
    """Raised before a run exceeds an explicitly configured resource boundary."""


@dataclass(frozen=True)
class BudgetLimits:
    max_model_calls: int = 80
    max_tool_calls: int = 160
    max_total_tokens: int = 500_000
    max_cost_usd: float = 50.0
    max_elapsed_seconds: float = 86_400.0
    max_identical_tool_calls: int = 2


@dataclass
class BudgetUsage:
    model_calls: int = 0
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class RunBudget:
    limits: BudgetLimits = field(default_factory=BudgetLimits)
    usage: BudgetUsage = field(default_factory=BudgetUsage)
    started_at: float = field(default_factory=monotonic)
    tool_fingerprints: Counter[str] = field(default_factory=Counter)

    def consume_model(
        self, *, input_tokens: int, output_tokens: int, estimated_cost_usd: float
    ) -> None:
        self._check_elapsed()
        candidate_calls = self.usage.model_calls + 1
        candidate_tokens = self.usage.total_tokens + input_tokens + output_tokens
        candidate_cost = self.usage.estimated_cost_usd + estimated_cost_usd
        if candidate_calls > self.limits.max_model_calls:
            raise BudgetExceeded("model call budget exceeded")
        if candidate_tokens > self.limits.max_total_tokens:
            raise BudgetExceeded("token budget exceeded")
        if candidate_cost > self.limits.max_cost_usd:
            raise BudgetExceeded("cost budget exceeded")
        self.usage.model_calls = candidate_calls
        self.usage.input_tokens += input_tokens
        self.usage.output_tokens += output_tokens
        self.usage.estimated_cost_usd = candidate_cost

    def consume_tool(self, fingerprint: str) -> None:
        self._check_elapsed()
        if self.usage.tool_calls + 1 > self.limits.max_tool_calls:
            raise BudgetExceeded("tool call budget exceeded")
        if (
            self.tool_fingerprints[fingerprint] + 1
            > self.limits.max_identical_tool_calls
        ):
            raise BudgetExceeded("identical tool call repetition budget exceeded")
        self.usage.tool_calls += 1
        self.tool_fingerprints[fingerprint] += 1

    def _check_elapsed(self) -> None:
        if monotonic() - self.started_at > self.limits.max_elapsed_seconds:
            raise BudgetExceeded("wall-clock budget exceeded")
