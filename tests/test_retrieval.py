from dataclasses import dataclass

import pytest

from paper_agents.retrieval import (
    AccessContext,
    EvidenceChunk,
    HybridRetriever,
    RankedCandidate,
)


@dataclass
class FakeRetriever:
    candidates: list[RankedCandidate]

    async def search(self, query: str, *, limit: int) -> list[RankedCandidate]:
        return self.candidates[:limit]


def candidate(chunk_id: str, score: float, principals: set[str]) -> RankedCandidate:
    return RankedCandidate(
        chunk=EvidenceChunk(
            chunk_id=chunk_id,
            document_id=f"doc-{chunk_id}",
            document_version="1",
            title=chunk_id,
            text=f"evidence {chunk_id}",
            source_uri=f"https://example.org/{chunk_id}",
            allowed_principals=principals,
        ),
        score=score,
    )


@pytest.mark.asyncio
async def test_hybrid_retrieval_fuses_channels_and_filters_acl() -> None:
    restricted = candidate("restricted", 1.0, {"team-secret"})
    shared = candidate("shared", 0.9, {"public"})
    sparse_only = candidate("sparse", 0.8, {"public"})
    dense_only = candidate("dense", 0.8, {"public"})
    retriever = HybridRetriever(
        sparse=FakeRetriever([restricted, shared, sparse_only]),
        dense=FakeRetriever([shared, dense_only, restricted]),
    )

    hits = await retriever.search(
        "research agents",
        access=AccessContext(subject_id="user-1"),
        limit=10,
    )

    assert [hit.chunk.chunk_id for hit in hits] == ["shared", "dense", "sparse"]
    assert hits[0].channels == ["bm25", "dense"]
    assert all(hit.chunk.chunk_id != "restricted" for hit in hits)


@pytest.mark.asyncio
async def test_retracted_evidence_never_enters_context() -> None:
    item = candidate("retracted", 1.0, {"public"})
    item.chunk.retracted = True
    retriever = HybridRetriever(
        sparse=FakeRetriever([item]), dense=FakeRetriever([item])
    )

    assert await retriever.search(
        "query", access=AccessContext(subject_id="user-1")
    ) == []
