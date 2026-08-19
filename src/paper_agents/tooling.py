from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from enum import StrEnum
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

from .budget import RunBudget


class ToolPolicyError(RuntimeError):
    pass


class ToolExecutionError(RuntimeError):
    pass


class TransientToolError(ToolExecutionError):
    pass


class ToolRisk(StrEnum):
    READ_ONLY = "read_only"
    WRITE_REVERSIBLE = "write_reversible"
    WRITE_IRREVERSIBLE = "write_irreversible"


class ToolCall(BaseModel):
    run_id: str
    task_id: str
    caller: str
    tool_name: str
    arguments: dict[str, Any]
    approved_gates: set[str] = Field(default_factory=set)
    idempotency_key: str | None = None


class ToolResult(BaseModel):
    tool_name: str
    output: dict[str, Any]
    attempts: int
    fingerprint: str
    replayed: bool = False


ToolHandler = Callable[[BaseModel], Awaitable[BaseModel]]


class ToolSpec(BaseModel):
    name: str
    description: str
    risk: ToolRisk = ToolRisk.READ_ONLY
    timeout_seconds: float = Field(default=15.0, gt=0)
    max_retries: int = Field(default=2, ge=0, le=5)
    required_gate: str | None = None
    idempotent: bool = True


class RegisteredTool:
    def __init__(
        self,
        *,
        spec: ToolSpec,
        input_model: type[BaseModel],
        output_model: type[BaseModel],
        handler: ToolHandler,
    ) -> None:
        self.spec = spec
        self.input_model = input_model
        self.output_model = output_model
        self.handler = handler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, tool: RegisteredTool) -> None:
        if tool.spec.name in self._tools:
            raise ValueError(f"Duplicate tool registration: {tool.spec.name}")
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> RegisteredTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolPolicyError(f"Tool is not allowlisted: {name}") from exc

    def schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": item.spec.name,
                "description": item.spec.description,
                "input_schema": item.input_model.model_json_schema(),
                "output_schema": item.output_model.model_json_schema(),
                "risk": item.spec.risk,
            }
            for item in self._tools.values()
        ]


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        budget: RunBudget | None = None,
        retry_base_seconds: float = 0.05,
    ) -> None:
        self.registry = registry
        self.budget = budget or RunBudget()
        self.retry_base_seconds = retry_base_seconds
        self._idempotency_results: dict[str, tuple[str, ToolResult]] = {}

    async def execute(self, call: ToolCall) -> ToolResult:
        tool = self.registry.get(call.tool_name)
        self._authorize(tool.spec, call)
        fingerprint = self._fingerprint(call)
        self.budget.consume_tool(fingerprint)

        if call.idempotency_key and call.idempotency_key in self._idempotency_results:
            stored_fingerprint, previous = self._idempotency_results[call.idempotency_key]
            if stored_fingerprint != fingerprint:
                raise ToolPolicyError(
                    "An idempotency_key cannot be reused with different arguments"
                )
            return previous.model_copy(update={"replayed": True})

        arguments = tool.input_model.model_validate(call.arguments)
        attempts = 0
        while True:
            attempts += 1
            try:
                async with asyncio.timeout(tool.spec.timeout_seconds):
                    raw_output = await tool.handler(arguments)
                output = tool.output_model.model_validate(raw_output)
                result = ToolResult(
                    tool_name=tool.spec.name,
                    output=output.model_dump(mode="json"),
                    attempts=attempts,
                    fingerprint=fingerprint,
                )
                if call.idempotency_key:
                    self._idempotency_results[call.idempotency_key] = (
                        fingerprint,
                        result,
                    )
                return result
            except TransientToolError:
                if attempts > tool.spec.max_retries:
                    raise
                await asyncio.sleep(self.retry_base_seconds * (2 ** (attempts - 1)))
            except TimeoutError as exc:
                if attempts > tool.spec.max_retries:
                    raise ToolExecutionError(
                        f"Tool {tool.spec.name} timed out after {attempts} attempts"
                    ) from exc
                await asyncio.sleep(self.retry_base_seconds * (2 ** (attempts - 1)))

    @staticmethod
    def _authorize(spec: ToolSpec, call: ToolCall) -> None:
        if spec.required_gate and spec.required_gate not in call.approved_gates:
            raise ToolPolicyError(
                f"Tool {spec.name} requires approval gate {spec.required_gate}"
            )
        if spec.risk != ToolRisk.READ_ONLY and not call.idempotency_key:
            raise ToolPolicyError(
                f"Write tool {spec.name} requires an idempotency_key"
            )
        if spec.risk == ToolRisk.WRITE_IRREVERSIBLE and not spec.required_gate:
            raise ToolPolicyError(
                f"Irreversible tool {spec.name} must declare a required_gate"
            )

    @staticmethod
    def _fingerprint(call: ToolCall) -> str:
        canonical = json.dumps(
            {"tool": call.tool_name, "arguments": call.arguments},
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return sha256(canonical.encode("utf-8")).hexdigest()
