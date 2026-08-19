from pathlib import Path

import pytest

from paper_agents.gateway import MockAgentGateway
from paper_agents.models import (
    ApprovalRequest,
    ExternalReviewInput,
    ResearchBrief,
    RunStatus,
)
from paper_agents.orchestrator import InvalidTransitionError, PaperOrchestrator


def brief(*, auto_approve: bool) -> ResearchBrief:
    return ResearchBrief(
        goal="验证一个端到端论文多智能体系统的编排、评审与返修闭环",
        domain="AI Agent Engineering",
        auto_approve=auto_approve,
    )


@pytest.mark.asyncio
async def test_complete_demo_runs_revision_loop(tmp_path: Path) -> None:
    orchestrator = PaperOrchestrator(
        db_path=tmp_path / "runs.db", gateway=MockAgentGateway()
    )
    state = await orchestrator.start(brief(auto_approve=True))

    assert state.status == RunStatus.COMPLETED
    assert state.revision_round == 1
    assert state.review_score is not None
    assert state.review_score >= state.review_threshold
    assert any(item.kind == "submission_package" for item in state.artifacts)
    assert any(event.event_type == "revision_round_completed" for event in state.events)


@pytest.mark.asyncio
async def test_human_gates_pause_and_resume(tmp_path: Path) -> None:
    orchestrator = PaperOrchestrator(
        db_path=tmp_path / "runs.db", gateway=MockAgentGateway()
    )
    state = await orchestrator.start(brief(auto_approve=False))
    assert state.status == RunStatus.WAITING_APPROVAL
    assert state.pending_gate == "research_plan"

    state = await orchestrator.approve(
        state.run_id,
        "research_plan",
        ApprovalRequest(
            decision="approve",
            reviewer="research-lead",
            artifact_sha256s=orchestrator.expected_gate_hashes(state, "research_plan"),
        ),
    )
    assert state.status == RunStatus.WAITING_APPROVAL
    assert state.pending_gate == "submission"

    state = await orchestrator.approve(
        state.run_id,
        "submission",
        ApprovalRequest(
            decision="approve",
            reviewer="corresponding-author",
            artifact_sha256s=orchestrator.expected_gate_hashes(state, "submission"),
        ),
    )
    assert state.status == RunStatus.COMPLETED


@pytest.mark.asyncio
async def test_checkpoint_can_be_loaded_by_new_orchestrator(tmp_path: Path) -> None:
    db_path = tmp_path / "runs.db"
    first = PaperOrchestrator(db_path=db_path, gateway=MockAgentGateway())
    paused = await first.start(brief(auto_approve=False))

    second = PaperOrchestrator(db_path=db_path, gateway=MockAgentGateway())
    restored = second.get_run(paused.run_id)
    assert restored.pending_gate == "research_plan"
    assert len(restored.artifacts) == len(paused.artifacts)
    assert second.store.list_events(paused.run_id)


@pytest.mark.asyncio
async def test_external_review_reopens_completed_run(tmp_path: Path) -> None:
    orchestrator = PaperOrchestrator(
        db_path=tmp_path / "runs.db", gateway=MockAgentGateway()
    )
    completed = await orchestrator.start(brief(auto_approve=True))
    revised = await orchestrator.ingest_external_review(
        completed.run_id,
        ExternalReviewInput(
            decision="major revision",
            comments=["补充消融实验", "解释统计功效并标注限制"],
        ),
    )
    assert revised.status == RunStatus.COMPLETED
    assert any(item.kind == "external_review" for item in revised.artifacts)
    assert any(item.kind == "rebuttal" for item in revised.artifacts)


@pytest.mark.asyncio
async def test_approval_rejects_changed_artifact_set(tmp_path: Path) -> None:
    orchestrator = PaperOrchestrator(
        db_path=tmp_path / "runs.db", gateway=MockAgentGateway()
    )
    state = await orchestrator.start(brief(auto_approve=False))

    with pytest.raises(InvalidTransitionError, match="exact artifact_sha256s"):
        await orchestrator.approve(
            state.run_id,
            "research_plan",
            ApprovalRequest(
                decision="approve",
                reviewer="research-lead",
                artifact_sha256s=["stale-or-tampered-hash"],
            ),
        )
