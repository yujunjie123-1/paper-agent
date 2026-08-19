import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from paper_agents.langgraph_runtime import GraphControlState, build_paper_graph


class FakeStageExecutor:
    async def execute_stage(
        self, stage_id: str, state: GraphControlState
    ) -> dict:
        if stage_id == "research_design":
            return {"gate_hashes": {"research_plan": ["protocol-hash"]}}
        if stage_id == "expert_review":
            return {
                "review_score": 0.5 if state.get("revision_round", 0) == 0 else 0.9
            }
        if stage_id == "revision":
            return {"revision_round": state.get("revision_round", 0) + 1}
        if stage_id == "submission_package":
            gate_hashes = dict(state.get("gate_hashes", {}))
            gate_hashes["submission"] = ["package-hash"]
            return {"gate_hashes": gate_hashes}
        return {}


@pytest.mark.asyncio
async def test_langgraph_control_plane_runs_revision_and_hash_bound_gates() -> None:
    graph = build_paper_graph(FakeStageExecutor(), checkpointer=InMemorySaver())
    result = await graph.ainvoke(
        {
            "run_id": "run-1",
            "review_score": None,
            "review_threshold": 0.78,
            "revision_round": 0,
            "max_revision_rounds": 2,
            "approvals": {
                "research_plan": {
                    "decision": "approve",
                    "artifact_sha256s": ["protocol-hash"],
                },
                "submission": {
                    "decision": "approve",
                    "artifact_sha256s": ["package-hash"],
                },
            },
            "gate_hashes": {},
            "executed_stages": [],
        },
        config={"configurable": {"thread_id": "run-1"}},
    )

    assert result["revision_round"] == 1
    assert result["review_score"] == 0.9
    assert result["executed_stages"].count("expert_review") == 2
    assert result["executed_stages"][-1] == "portal_submission"


@pytest.mark.asyncio
async def test_langgraph_interrupts_resume_both_human_gates() -> None:
    graph = build_paper_graph(FakeStageExecutor(), checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "run-hitl"}}
    initial = {
        "run_id": "run-hitl",
        "review_score": None,
        "review_threshold": 0.78,
        "revision_round": 0,
        "max_revision_rounds": 2,
        "approvals": {},
        "gate_hashes": {},
        "executed_stages": [],
    }

    research_pause = await graph.ainvoke(initial, config=config)
    research_request = research_pause["__interrupt__"][0].value
    assert research_request["gate"] == "research_plan"
    assert research_request["artifact_sha256s"] == ["protocol-hash"]

    submission_pause = await graph.ainvoke(
        Command(
            resume={
                "decision": "approve",
                "artifact_sha256s": ["protocol-hash"],
            }
        ),
        config=config,
    )
    submission_request = submission_pause["__interrupt__"][0].value
    assert submission_request["gate"] == "submission"
    assert submission_request["artifact_sha256s"] == ["package-hash"]

    completed = await graph.ainvoke(
        Command(
            resume={
                "decision": "approve",
                "artifact_sha256s": ["package-hash"],
            }
        ),
        config=config,
    )
    assert completed["executed_stages"][-1] == "portal_submission"
