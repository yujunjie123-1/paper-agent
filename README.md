# paper-agent

Durable, review-driven multi-agent workflow for the research paper lifecycle.

`paper-agent` turns a research brief into a checkpointed workflow covering venue discovery, evidence retrieval, study design, experiment planning, scientific writing, independent review, revision, rebuttal, and submission-package approval. The control plane owns state, permissions, budgets, and side effects; language models handle bounded semantic tasks behind typed contracts.

## Project snapshot

| Area | Current release | Evidence in this repository |
| --- | --- | --- |
| Workflow | LangGraph runtime plus native reference runtime | `src/paper_agents/`, `config/workflow.yaml` |
| Agent roles | 30 specialized roles across research, retrieval, experiment, writing, review, and submission | `config/agents.yaml` |
| Review loop | Six independent review lenses, arbitration, revision, and re-review | `src/paper_agents/orchestrator.py` |
| Retrieval | ACL filtering, BM25 + dense channels, reciprocal-rank fusion, conditional reranking | `src/paper_agents/retrieval.py` |
| Governance | JSON tool contracts, risk gates, idempotency checks, retries, circuit boundaries, and run budgets | `src/paper_agents/tooling.py`, `src/paper_agents/budget.py` |
| Delivery | FastAPI, CLI, health endpoint, Docker Compose, structured traces | `src/paper_agents/api.py`, `compose.yaml` |

## Outcomes and reach

- Shared with more than 100 users through research, competition, and project preparation sessions.
- Helped multiple participants complete academic competition materials and obtain second-prize and third-prize outcomes.
- The local validation run covers 22 automated tests, one revision round, 36 generated artifacts, and 105 recorded workflow events.
- The deployment profile includes a single-node FastAPI container, persistent SQLite volume, health checks, bounded budgets, and a documented path to Postgres/pgvector, Redis, object storage, and worker separation.
- Venue selection, submission checks, reviewer response, and package-hash approval are implemented as traceable workflow stages. Certificates, acceptance notices, and deployment records can be added under `docs/evidence/`.

## Architecture

```text
Research brief
      |
      v
Deterministic workflow graph
      |
      +--> venue intelligence ------+
      +--> retrieval + evidence -----+--> research plan gate
      +--> study design ------------+
      +--> experiment + statistics --+
      +--> scientific writing ------+--> six-lens review
                                              |
                                   arbitration + revision
                                              |
                                    submission package gate
```

Key design choices:

- durable checkpoints are written at every workflow node;
- parallel fan-out is limited to independent research and review tasks;
- artifacts are immutable, versioned, and hash-addressed;
- approvals carry the expected artifact hashes to detect replacement;
- retrieval filters access before context construction;
- unsupported claims and evidence conflicts enter a review queue;
- external browser or submission actions stay behind explicit human gates.

## Quick start

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

The checked-in `.env` contains local mock-provider defaults. The application reads configuration from process environment variables, so load the file in your shell before starting the API:

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -and $_ -notmatch '^\s*#') {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
  }
}
.venv\Scripts\uvicorn paper_agents.api:app --reload
```

Then open `http://127.0.0.1:8000/docs` and check `http://127.0.0.1:8000/health`.

For a real model provider, set `PAPER_AGENTS_PROVIDER=openai`, provide `OPENAI_API_KEY` through your shell or secret manager, and keep human approval enabled for research and submission gates.

## CLI and API

```powershell
.venv\Scripts\paper-agents run
.venv\Scripts\paper-agents show RUN_ID
.venv\Scripts\paper-agents approve RUN_ID research_plan
```

The API exposes:

- `POST /v1/runs` to create a research run;
- `GET /v1/runs/{run_id}` to read state, artifacts, and events;
- `POST /v1/runs/{run_id}/approvals/{gate}` to approve a research-plan or submission gate;
- `POST /v1/runs/{run_id}/external-reviews` to start a rebuttal and revision loop;
- `GET /.well-known/agent-card.json` for capability discovery.

## Deployment

```powershell
docker compose up --build
Invoke-RestMethod http://localhost:8000/health
```

The Compose profile stores run state in a named volume and runs the API as a non-root user. The production topology and rollback sequence are documented in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). The repository keeps the local profile reproducible and makes the multi-worker production expansion explicit in configuration.

## Evaluation

The evaluation plan compares native-single, native-multi, langgraph-single, langgraph-multi, and request-multi-stage variants on the same cases. Primary metrics are task success and blocker-defect recall; secondary metrics include retrieval ranking, citation precision, tool selection, crash-resume success, P95 latency, token usage, and estimated cost. See [`docs/EVALUATION_PLAN.md`](docs/EVALUATION_PLAN.md).

## Academic references

The project maintains a curated list of competitions, benchmarks, and journals relevant to scholarly agent systems in [`docs/ACADEMIC_REFERENCES.md`](docs/ACADEMIC_REFERENCES.md).

## Evidence index

Use [`docs/evidence/README.md`](docs/evidence/README.md) for certificates, award announcements, deployment records, acceptance notices, and anonymized feedback summaries. The index keeps public claims traceable without placing private user data in the repository.

## License

MIT. See [`LICENSE`](LICENSE).
