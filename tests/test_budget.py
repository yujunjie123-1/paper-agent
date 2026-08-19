import pytest

from paper_agents.budget import BudgetExceeded, BudgetLimits, RunBudget


def test_model_budget_rejects_before_mutating_usage() -> None:
    budget = RunBudget(
        limits=BudgetLimits(max_model_calls=1, max_total_tokens=10, max_cost_usd=1)
    )
    budget.consume_model(input_tokens=4, output_tokens=5, estimated_cost_usd=0.2)

    with pytest.raises(BudgetExceeded, match="model call"):
        budget.consume_model(input_tokens=0, output_tokens=0, estimated_cost_usd=0)

    assert budget.usage.model_calls == 1
    assert budget.usage.total_tokens == 9


def test_repeated_tool_fingerprint_stops_agent_loop() -> None:
    budget = RunBudget(limits=BudgetLimits(max_identical_tool_calls=2))
    budget.consume_tool("same-call")
    budget.consume_tool("same-call")

    with pytest.raises(BudgetExceeded, match="repetition"):
        budget.consume_tool("same-call")
