import pytest
from pydantic import BaseModel

from paper_agents.tooling import (
    RegisteredTool,
    ToolCall,
    ToolExecutor,
    ToolPolicyError,
    ToolRegistry,
    ToolRisk,
    ToolSpec,
    TransientToolError,
)


class Input(BaseModel):
    value: int


class Output(BaseModel):
    doubled: int


def call(*, arguments=None, gates=None, key="idem-1") -> ToolCall:
    return ToolCall(
        run_id="run-1",
        task_id="task-1",
        caller="portal_operator",
        tool_name="submit",
        arguments=arguments or {"value": 2},
        approved_gates=gates or set(),
        idempotency_key=key,
    )


@pytest.mark.asyncio
async def test_write_tool_requires_gate_and_idempotency() -> None:
    async def handler(value: Input) -> Output:
        return Output(doubled=value.value * 2)

    registry = ToolRegistry()
    registry.register(
        RegisteredTool(
            spec=ToolSpec(
                name="submit",
                description="submit exact approved package",
                risk=ToolRisk.WRITE_IRREVERSIBLE,
                required_gate="submission",
            ),
            input_model=Input,
            output_model=Output,
            handler=handler,
        )
    )
    executor = ToolExecutor(registry, retry_base_seconds=0)

    with pytest.raises(ToolPolicyError, match="requires approval"):
        await executor.execute(call())
    with pytest.raises(ToolPolicyError, match="idempotency_key"):
        await executor.execute(call(gates={"submission"}, key=None))


@pytest.mark.asyncio
async def test_transient_retry_and_idempotent_replay() -> None:
    attempts = 0

    async def handler(value: Input) -> Output:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TransientToolError("temporary")
        return Output(doubled=value.value * 2)

    registry = ToolRegistry()
    registry.register(
        RegisteredTool(
            spec=ToolSpec(
                name="submit",
                description="submit",
                risk=ToolRisk.WRITE_IRREVERSIBLE,
                required_gate="submission",
                max_retries=1,
            ),
            input_model=Input,
            output_model=Output,
            handler=handler,
        )
    )
    executor = ToolExecutor(registry, retry_base_seconds=0)

    first = await executor.execute(call(gates={"submission"}))
    replay = await executor.execute(call(gates={"submission"}))

    assert first.attempts == 2
    assert replay.replayed is True
    assert attempts == 2

    with pytest.raises(ToolPolicyError, match="different arguments"):
        await executor.execute(
            call(arguments={"value": 3}, gates={"submission"})
        )
