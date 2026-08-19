# paper-agent 0.3.0

This release packages the V2 durable workflow as the public project line.

- primary runtime: LangGraph-backed workflow with a native Python reference path;
- control-plane guarantees: checkpointed state, approval gates, artifact hashes, bounded retries, and replay-safe transitions;
- retrieval baseline: ACL filtering, BM25 + dense retrieval, reciprocal-rank fusion, conditional reranking, and conflict quarantine;
- delivery surface: FastAPI, CLI, Docker Compose, structured traces, and offline evaluation contracts.

The historical V1 implementation is retained in the source workspace for comparison and is excluded from the public release.
