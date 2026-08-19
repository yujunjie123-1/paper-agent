from __future__ import annotations

import operator
from typing import Annotated, Any, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class GraphControlState(TypedDict, total=False):
    run_id: str
    current_stage: str
    review_score: float | None
    review_threshold: float
    revision_round: int
    max_revision_rounds: int
    approvals: dict[str, dict[str, Any]]
    gate_hashes: dict[str, list[str]]
    executed_stages: Annotated[list[str], operator.add]


class StageExecutor(Protocol):
    async def execute_stage(
        self, stage_id: str, state: GraphControlState
    ) -> dict[str, Any]: ...


def build_paper_graph(executor: StageExecutor, *, checkpointer=None):
    """Compile the V2 control graph while keeping domain work behind a port."""

    builder = StateGraph(GraphControlState)

    def stage_node(stage_id: str):
        async def run(state: GraphControlState) -> dict[str, Any]:
            update = await executor.execute_stage(stage_id, state)
            return {
                **update,
                "current_stage": stage_id,
                "executed_stages": [stage_id],
            }

        return run

    def gate_node(gate: str):
        def run(state: GraphControlState) -> dict[str, Any]:
            expected = sorted(state.get("gate_hashes", {}).get(gate, []))
            existing = state.get("approvals", {}).get(gate)
            if existing is None:
                existing = interrupt(
                    {
                        "gate": gate,
                        "artifact_sha256s": expected,
                        "instruction": "Approve or reject this exact artifact set",
                    }
                )
            if existing.get("decision") != "approve":
                raise RuntimeError(f"Gate {gate} was not approved")
            if sorted(existing.get("artifact_sha256s", [])) != expected:
                raise RuntimeError(f"Gate {gate} approval hashes do not match")
            approvals = {**state.get("approvals", {}), gate: existing}
            return {
                "approvals": approvals,
                "current_stage": f"{gate}_approval",
                "executed_stages": [f"{gate}_approval"],
            }

        return run

    stage_ids = [
        "venue_research",
        "topic_selection",
        "literature_review",
        "research_design",
        "experimentation",
        "manuscript",
        "expert_review",
        "revision",
        "submission_package",
        "portal_submission",
    ]
    for stage_id in stage_ids:
        builder.add_node(stage_id, stage_node(stage_id))
    builder.add_node("research_plan_approval", gate_node("research_plan"))
    builder.add_node("submission_approval", gate_node("submission"))

    builder.add_edge(START, "venue_research")
    builder.add_edge("venue_research", "topic_selection")
    builder.add_edge("topic_selection", "literature_review")
    builder.add_edge("literature_review", "research_design")
    builder.add_edge("research_design", "research_plan_approval")
    builder.add_edge("research_plan_approval", "experimentation")
    builder.add_edge("experimentation", "manuscript")
    builder.add_edge("manuscript", "expert_review")

    def route_review(state: GraphControlState) -> str:
        score = state.get("review_score")
        threshold = state.get("review_threshold", 0.78)
        revision_round = state.get("revision_round", 0)
        max_rounds = state.get("max_revision_rounds", 2)
        if score is not None and score >= threshold:
            return "submission_package"
        if revision_round >= max_rounds:
            return "submission_package"
        return "revision"

    builder.add_conditional_edges(
        "expert_review",
        route_review,
        {
            "revision": "revision",
            "submission_package": "submission_package",
        },
    )
    builder.add_edge("revision", "expert_review")
    builder.add_edge("submission_package", "submission_approval")
    builder.add_edge("submission_approval", "portal_submission")
    builder.add_edge("portal_submission", END)
    return builder.compile(checkpointer=checkpointer)
