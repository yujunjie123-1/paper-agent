from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "password",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


class TraceEvent(BaseModel):
    trace_id: str
    span_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    parent_span_id: str | None = None
    run_id: str
    task_id: str | None = None
    stage_id: str | None = None
    agent_id: str | None = None
    event_name: str
    status: str = "ok"
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class TraceRecorder:
    """Local test recorder using OpenTelemetry-compatible identifiers and attributes."""

    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def record(self, event: TraceEvent) -> TraceEvent:
        safe = event.model_copy(update={"attributes": redact(event.attributes)})
        self.events.append(safe)
        return safe

    def for_run(self, run_id: str) -> list[TraceEvent]:
        return [event for event in self.events if event.run_id == run_id]
