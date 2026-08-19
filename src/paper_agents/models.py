from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(StrEnum):
    BLOCKER = "blocker"
    MAJOR = "major"
    MINOR = "minor"
    NOTE = "note"


class ResearchBrief(BaseModel):
    goal: str = Field(min_length=10)
    domain: str = Field(min_length=2)
    intended_output: str = "research paper"
    candidate_venues: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    seed_sources: list[str] = Field(default_factory=list)
    auto_approve: bool = False


class ApprovalRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    note: str = ""
    reviewer: str = "human"
    artifact_sha256s: list[str] = Field(default_factory=list)


class ExternalReviewInput(BaseModel):
    source: str = "external-review"
    decision: str | None = None
    comments: list[str] = Field(min_length=1)


class ReviewIssue(BaseModel):
    issue_id: str = Field(default_factory=lambda: str(uuid4()))
    severity: Severity
    dimension: str
    location: str
    finding: str
    evidence: str
    required_action: str
    confidence: float = Field(ge=0, le=1)


class AgentSpec(BaseModel):
    id: str
    role: str
    phase: str
    objective: str
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    output_kind: str
    max_steps: int = Field(default=8, ge=1, le=32)


class AgentTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    stage_id: str
    agent_id: str
    artifact_ids: list[str] = Field(default_factory=list)
    revision_round: int = 0


class AgentResult(BaseModel):
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    citations: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    review_score: float | None = Field(default=None, ge=0, le=1)
    issues: list[ReviewIssue] = Field(default_factory=list)


class Artifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    kind: str
    producer: str
    stage_id: str
    version: int = 1
    content: dict[str, Any]
    citations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    created_at: datetime = Field(default_factory=utc_now)
    content_sha256: str = ""

    @model_validator(mode="after")
    def compute_hash(self) -> "Artifact":
        if not self.content_sha256:
            canonical = self.model_dump_json(
                exclude={"artifact_id", "created_at", "content_sha256"}
            )
            self.content_sha256 = sha256(canonical.encode("utf-8")).hexdigest()
        return self


class WorkflowEvent(BaseModel):
    event_type: str
    stage_id: str | None = None
    agent_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class RunState(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str = "paper-lifecycle-2026"
    status: RunStatus = RunStatus.CREATED
    brief: ResearchBrief
    stage_index: int = 0
    current_stage: str | None = None
    pending_gate: str | None = None
    approvals: dict[str, dict[str, Any]] = Field(default_factory=dict)
    revision_round: int = 0
    max_revision_rounds: int = 2
    review_threshold: float = Field(default=0.78, ge=0, le=1)
    review_score: float | None = None
    artifacts: list[Artifact] = Field(default_factory=list)
    events: list[WorkflowEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    error: str | None = None

    def latest_artifacts(self, kinds: set[str] | None = None) -> list[Artifact]:
        selected = self.artifacts
        if kinds:
            selected = [artifact for artifact in selected if artifact.kind in kinds]
        return selected
