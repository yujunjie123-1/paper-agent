# Release validation

## Verified in the release workspace

| Check | Result | Coverage |
| --- | --- | --- |
| Python compilation | passed | `src/` and `tests/` compile cleanly on Python 3.12. |
| Core automated suite | 20 passed | API contracts, browser policy, budgets, retrieval, observability, orchestration, and tool governance. |
| LangGraph integration suite | source included; runner requires the matching LangGraph runtime | `tests/test_langgraph_runtime.py` covers graph compilation, interrupts, checkpoints, and resume behavior. |
| Local lifecycle run | completed | Research brief, fan-out/fan-in stages, approval flow, revision loop, artifacts, and event trace. |
| Package metadata | passed | Editable project metadata, CLI entry point, Docker files, and CI workflow are present. |
| Release audit | passed | No workstation paths, private interview inputs, local databases, caches, or secrets are tracked. |

The release workspace records one revision round, 36 generated artifacts, and 105 workflow events for the local lifecycle run. Those figures describe the repository validation path; quality and acceptance claims require a fixed dataset and the evaluation protocol in `docs/EVALUATION_PLAN.md`.

## Production acceptance checklist

- Run the full LangGraph suite with the project dependency lock on Python 3.11, 3.12, and 3.13.
- Run single-agent and multi-agent comparisons on the same 30-100 case dataset.
- Record task success, blocker-defect recall, citation precision, crash-resume success, P95 latency, tokens, and cost.
- Complete Postgres/pgvector, queue, object-storage, worker, Docker/Linux, and rollback acceptance.
- Add public deployment, award, or acceptance records under `docs/evidence/` before using them as external proof.
