from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .models import ApprovalRequest, ExternalReviewInput, ResearchBrief, RunState
from .orchestrator import InvalidTransitionError, PaperOrchestrator, RunNotFoundError


app = FastAPI(
    title="Paper Agent Lab",
    version="0.1.0",
    description="Durable research lifecycle multi-agent orchestrator",
)
orchestrator = PaperOrchestrator()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/runs", response_model=RunState)
async def create_run(brief: ResearchBrief) -> RunState:
    return await orchestrator.start(brief)


@app.get("/v1/runs/{run_id}", response_model=RunState)
async def get_run(run_id: str) -> RunState:
    try:
        return orchestrator.get_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc


@app.get("/v1/runs/{run_id}/events")
async def get_events(run_id: str) -> list[dict]:
    try:
        orchestrator.get_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc
    return orchestrator.store.list_events(run_id)


@app.post("/v1/runs/{run_id}/approvals/{gate}", response_model=RunState)
async def approve_run(run_id: str, gate: str, request: ApprovalRequest) -> RunState:
    try:
        return await orchestrator.approve(run_id, gate, request)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/runs/{run_id}/external-reviews", response_model=RunState)
async def external_review(run_id: str, review: ExternalReviewInput) -> RunState:
    try:
        return await orchestrator.ingest_external_review(run_id, review)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/.well-known/agent-card.json")
async def agent_card() -> dict:
    return {
        "name": "Paper Agent Lab Coordinator",
        "description": "Coordinates venue research, literature, experiments, writing, expert review and revision.",
        "supportedInterfaces": [
            {
                "url": "/v1",
                "protocolBinding": "HTTP+JSON",
                "protocolVersion": "1.0",
            }
        ],
        "version": "0.1.0",
        "capabilities": {"streaming": False, "extendedAgentCard": False},
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [
            {
                "id": "paper-lifecycle",
                "name": "Paper lifecycle",
                "description": "Run a durable research-to-submission workflow with human approval gates.",
                "tags": ["research", "paper", "peer-review", "revision"],
            }
        ],
        "securitySchemes": {},
        "documentationUrl": "/docs",
        "x-compliance-note": "Discovery card only; full A2A task operations are not implemented in this MVP.",
    }

