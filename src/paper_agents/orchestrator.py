from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Settings, load_agent_specs, load_workflow
from .gateway import AgentGateway, MockAgentGateway, OpenAIResponsesGateway
from .models import (
    AgentResult,
    AgentTask,
    ApprovalRequest,
    Artifact,
    ExternalReviewInput,
    ResearchBrief,
    RunState,
    RunStatus,
    WorkflowEvent,
)
from .store import SQLiteRunStore


class RunNotFoundError(KeyError):
    pass


class InvalidTransitionError(RuntimeError):
    pass


class PaperOrchestrator:
    def __init__(
        self,
        *,
        db_path: Path | None = None,
        gateway: AgentGateway | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.workflow = load_workflow()
        self.agent_specs = load_agent_specs()
        self.store = SQLiteRunStore(db_path or self.settings.db_path)
        if gateway is not None:
            self.gateway = gateway
        elif self.settings.provider == "openai":
            self.gateway = OpenAIResponsesGateway(self.settings.openai_model)
        else:
            self.gateway = MockAgentGateway()

    def create_run(self, brief: ResearchBrief) -> RunState:
        state = RunState(
            brief=brief,
            max_revision_rounds=self.settings.max_revisions,
            review_threshold=self.settings.review_threshold,
        )
        self._record(state, "run_created", payload={"brief": brief.model_dump(mode="json")})
        self._checkpoint(state)
        return state

    def get_run(self, run_id: str) -> RunState:
        state = self.store.load(run_id)
        if state is None:
            raise RunNotFoundError(run_id)
        return state

    async def start(self, brief: ResearchBrief) -> RunState:
        state = self.create_run(brief)
        return await self.run_until_pause(state.run_id)

    async def run_until_pause(self, run_id: str) -> RunState:
        state = self.get_run(run_id)
        if state.status == RunStatus.COMPLETED:
            return state
        if state.status == RunStatus.WAITING_APPROVAL and state.pending_gate:
            return state
        if state.status == RunStatus.FAILED:
            raise InvalidTransitionError(f"Run {run_id} is failed: {state.error}")

        state.status = RunStatus.RUNNING
        stages: list[dict[str, Any]] = self.workflow["stages"]
        try:
            while state.stage_index < len(stages):
                stage = stages[state.stage_index]
                state.current_stage = stage["id"]
                self._record(state, "stage_started", stage_id=stage["id"])
                self._checkpoint(state)

                mode = stage["mode"]
                if mode == "parallel_then_adjudicate":
                    await self._run_parallel_stage(state, stage)
                elif mode == "sequential":
                    await self._run_sequential_agents(state, stage["id"], stage["agents"])
                elif mode == "human_gate":
                    should_pause = self._process_gate(state, stage["gate"])
                    if should_pause:
                        return state
                elif mode == "conditional_loop":
                    await self._process_revision_loop(state, stage, stages)
                    if state.stage_index != stages.index(stage):
                        continue
                else:
                    raise ValueError(f"Unsupported workflow mode: {mode}")

                self._record(state, "stage_completed", stage_id=stage["id"])
                state.stage_index += 1
                self._checkpoint(state)

            state.status = RunStatus.COMPLETED
            state.current_stage = "completed"
            state.pending_gate = None
            self._record(state, "run_completed")
            self._checkpoint(state)
            return state
        except Exception as exc:
            state.status = RunStatus.FAILED
            state.error = f"{type(exc).__name__}: {exc}"
            self._record(state, "run_failed", payload={"error": state.error})
            self._checkpoint(state)
            raise

    async def approve(self, run_id: str, gate: str, request: ApprovalRequest) -> RunState:
        state = self.get_run(run_id)
        if state.status != RunStatus.WAITING_APPROVAL or state.pending_gate != gate:
            raise InvalidTransitionError(
                f"Run is waiting for {state.pending_gate!r}, not {gate!r}"
            )
        expected_hashes = self.expected_gate_hashes(state, gate)
        if request.decision == "approve" and sorted(request.artifact_sha256s) != expected_hashes:
            raise InvalidTransitionError(
                "Approval must echo the exact artifact_sha256s shown by the pending gate"
            )
        state.approvals[gate] = {
            "decision": request.decision,
            "note": request.note,
            "reviewer": request.reviewer,
            "artifact_sha256s": expected_hashes,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self._record(
            state,
            "approval_recorded",
            stage_id=state.current_stage,
            payload={"gate": gate, **state.approvals[gate]},
        )
        if request.decision == "reject":
            state.status = RunStatus.FAILED
            state.error = f"Human rejected gate {gate}: {request.note}"
            state.pending_gate = None
            self._checkpoint(state)
            return state

        state.status = RunStatus.RUNNING
        state.pending_gate = None
        state.stage_index += 1
        self._checkpoint(state)
        return await self.run_until_pause(run_id)

    async def ingest_external_review(
        self, run_id: str, review: ExternalReviewInput
    ) -> RunState:
        state = self.get_run(run_id)
        if state.status not in {RunStatus.COMPLETED, RunStatus.WAITING_APPROVAL}:
            raise InvalidTransitionError("External review can only enter a stable or approval state")
        artifact = Artifact(
            run_id=run_id,
            kind="external_review",
            producer="human_external_reviewer",
            stage_id="external_review",
            content=review.model_dump(mode="json"),
            confidence=1.0,
        )
        state.artifacts.append(artifact)
        state.approvals.pop("submission", None)
        state.pending_gate = None
        state.status = RunStatus.RUNNING
        state.current_stage = "external_review_revision"
        self._record(
            state,
            "external_review_ingested",
            stage_id="external_review_revision",
            payload={"artifact_id": artifact.artifact_id, "comment_count": len(review.comments)},
        )
        await self._run_sequential_agents(
            state,
            "external_review_revision",
            self.workflow["external_review_flow"]["agents"],
        )
        state.revision_round += 1
        review_index = next(
            index
            for index, stage in enumerate(self.workflow["stages"])
            if stage["id"] == self.workflow["external_review_flow"]["then"]
        )
        state.stage_index = review_index
        self._checkpoint(state)
        return await self.run_until_pause(run_id)

    async def _run_parallel_stage(self, state: RunState, stage: dict[str, Any]) -> None:
        input_artifacts = list(state.artifacts)
        coroutines = [
            self._execute_agent(state, stage["id"], agent_id, input_artifacts, commit=False)
            for agent_id in stage["agents"]
        ]
        results = await asyncio.gather(*coroutines)
        for agent_id, result in zip(stage["agents"], results, strict=True):
            self._commit_result(state, stage["id"], agent_id, result)
        await self._execute_agent(state, stage["id"], stage["join"], list(state.artifacts))

    async def _run_sequential_agents(
        self, state: RunState, stage_id: str, agent_ids: list[str]
    ) -> None:
        for agent_id in agent_ids:
            await self._execute_agent(state, stage_id, agent_id, list(state.artifacts))

    async def _execute_agent(
        self,
        state: RunState,
        stage_id: str,
        agent_id: str,
        artifacts: list[Artifact],
        *,
        commit: bool = True,
    ) -> AgentResult:
        spec = self.agent_specs[agent_id]
        task = AgentTask(
            run_id=state.run_id,
            stage_id=stage_id,
            agent_id=agent_id,
            artifact_ids=[item.artifact_id for item in artifacts[-12:]],
            revision_round=state.revision_round,
        )
        self._record(
            state,
            "agent_started",
            stage_id=stage_id,
            agent_id=agent_id,
            payload={"task_id": task.task_id, "max_steps": spec.max_steps},
        )
        result = await self.gateway.execute(spec, task, artifacts)
        if commit:
            self._commit_result(state, stage_id, agent_id, result)
        return result

    def _commit_result(
        self, state: RunState, stage_id: str, agent_id: str, result: AgentResult
    ) -> None:
        spec = self.agent_specs[agent_id]
        version = 1 + sum(
            1
            for artifact in state.artifacts
            if artifact.kind == spec.output_kind and artifact.producer == agent_id
        )
        content = {
            "summary": result.summary,
            **result.payload,
            "review_score": result.review_score,
            "issues": [issue.model_dump(mode="json") for issue in result.issues],
        }
        artifact = Artifact(
            run_id=state.run_id,
            kind=spec.output_kind,
            producer=agent_id,
            stage_id=stage_id,
            version=version,
            content=content,
            citations=result.citations,
            confidence=result.confidence,
        )
        state.artifacts.append(artifact)
        if spec.output_kind == "review_decision" and result.review_score is not None:
            state.review_score = result.review_score
        self._record(
            state,
            "agent_completed",
            stage_id=stage_id,
            agent_id=agent_id,
            payload={
                "artifact_id": artifact.artifact_id,
                "kind": artifact.kind,
                "version": artifact.version,
                "sha256": artifact.content_sha256,
            },
        )
        self._checkpoint(state)

    def _process_gate(self, state: RunState, gate: str) -> bool:
        existing = state.approvals.get(gate)
        if existing and existing["decision"] == "approve":
            return False
        if state.brief.auto_approve or self.settings.auto_approve:
            expected_hashes = self.expected_gate_hashes(state, gate)
            state.approvals[gate] = {
                "decision": "approve",
                "note": "demo auto-approval",
                "reviewer": "system-demo",
                "artifact_sha256s": expected_hashes,
                "at": datetime.now(timezone.utc).isoformat(),
            }
            self._record(
                state,
                "gate_auto_approved",
                payload={"gate": gate, "artifact_sha256s": expected_hashes},
            )
            return False
        state.status = RunStatus.WAITING_APPROVAL
        state.pending_gate = gate
        self._record(
            state,
            "approval_required",
            payload={
                "gate": gate,
                "artifact_sha256s": self.expected_gate_hashes(state, gate),
            },
        )
        self._checkpoint(state)
        return True

    @staticmethod
    def expected_gate_hashes(state: RunState, gate: str) -> list[str]:
        """Return the immutable artifact set a human is approving at this gate."""
        if gate == "research_plan":
            kinds = {
                "venue_decision",
                "topic_decision",
                "evidence_ledger",
                "preregistered_protocol",
            }
        elif gate == "submission":
            kinds = {"submission_package"}
        else:
            raise InvalidTransitionError(f"Unknown approval gate: {gate}")
        return sorted(
            artifact.content_sha256
            for artifact in state.artifacts
            if artifact.kind in kinds
        )

    async def _process_revision_loop(
        self,
        state: RunState,
        stage: dict[str, Any],
        stages: list[dict[str, Any]],
    ) -> None:
        if state.review_score is not None and state.review_score >= state.review_threshold:
            self._record(
                state,
                "review_threshold_met",
                stage_id=stage["id"],
                payload={"score": state.review_score, "threshold": state.review_threshold},
            )
            return
        if state.revision_round >= state.max_revision_rounds:
            self._record(
                state,
                "revision_limit_reached",
                stage_id=stage["id"],
                payload={
                    "score": state.review_score,
                    "max_revision_rounds": state.max_revision_rounds,
                    "requires_human_risk_acceptance": True,
                },
            )
            return
        await self._run_sequential_agents(state, stage["id"], stage["agents"])
        state.revision_round += 1
        target_index = next(
            index for index, item in enumerate(stages) if item["id"] == stage["target"]
        )
        self._record(
            state,
            "revision_round_completed",
            stage_id=stage["id"],
            payload={"revision_round": state.revision_round, "next_stage": stage["target"]},
        )
        state.stage_index = target_index
        self._checkpoint(state)

    def _record(
        self,
        state: RunState,
        event_type: str,
        *,
        stage_id: str | None = None,
        agent_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event = WorkflowEvent(
            event_type=event_type,
            stage_id=stage_id,
            agent_id=agent_id,
            payload=payload or {},
        )
        state.events.append(event)
        self.store.append_event(state.run_id, event)

    def _checkpoint(self, state: RunState) -> None:
        state.updated_at = datetime.now(timezone.utc)
        self.store.save(state)
