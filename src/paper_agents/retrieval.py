from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Protocol

from pydantic import BaseModel, Field


class AccessContext(BaseModel):
    subject_id: str
    principals: set[str] = Field(default_factory=set)

    def all_principals(self) -> set[str]:
        return {self.subject_id, "public", *self.principals}


class EvidenceChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_version: str
    title: str
    text: str
    source_uri: str
    page: int | None = None
    allowed_principals: set[str] = Field(default_factory=lambda: {"public"})
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    retracted: bool = False

    def visible_to(self, access: AccessContext, now: datetime | None = None) -> bool:
        at = now or datetime.now(timezone.utc)
        if self.retracted or not (self.allowed_principals & access.all_principals()):
            return False
        if self.valid_from and at < self.valid_from:
            return False
        return not self.valid_until or at <= self.valid_until


class RankedCandidate(BaseModel):
    chunk: EvidenceChunk
    score: float


class RetrievalHit(BaseModel):
    chunk: EvidenceChunk
    fused_score: float
    channels: list[str]
    channel_ranks: dict[str, int]


class Retriever(Protocol):
    async def search(self, query: str, *, limit: int) -> list[RankedCandidate]: ...


class Reranker(Protocol):
    async def rerank(
        self, query: str, candidates: list[RetrievalHit]
    ) -> list[RetrievalHit]: ...


def reciprocal_rank_fusion(
    rankings: dict[str, list[RankedCandidate]],
    *,
    access: AccessContext,
    rank_constant: int = 60,
    limit: int = 10,
) -> list[RetrievalHit]:
    scores: defaultdict[str, float] = defaultdict(float)
    chunks: dict[str, EvidenceChunk] = {}
    channels: defaultdict[str, set[str]] = defaultdict(set)
    ranks: defaultdict[str, dict[str, int]] = defaultdict(dict)

    for channel, candidates in rankings.items():
        visible_rank = 0
        for candidate in candidates:
            if not candidate.chunk.visible_to(access):
                continue
            visible_rank += 1
            chunk_id = candidate.chunk.chunk_id
            chunks[chunk_id] = candidate.chunk
            channels[chunk_id].add(channel)
            ranks[chunk_id][channel] = visible_rank
            scores[chunk_id] += 1.0 / (rank_constant + visible_rank)

    ordered_ids = sorted(scores, key=lambda item: (-scores[item], item))[:limit]
    return [
        RetrievalHit(
            chunk=chunks[chunk_id],
            fused_score=scores[chunk_id],
            channels=sorted(channels[chunk_id]),
            channel_ranks=ranks[chunk_id],
        )
        for chunk_id in ordered_ids
    ]


class HybridRetriever:
    def __init__(
        self,
        *,
        sparse: Retriever,
        dense: Retriever,
        reranker: Reranker | None = None,
        rank_constant: int = 60,
    ) -> None:
        self.sparse = sparse
        self.dense = dense
        self.reranker = reranker
        self.rank_constant = rank_constant

    async def search(
        self,
        query: str,
        *,
        access: AccessContext,
        limit: int = 10,
        rerank: bool = False,
    ) -> list[RetrievalHit]:
        sparse, dense = await asyncio.gather(
            self.sparse.search(query, limit=limit * 3),
            self.dense.search(query, limit=limit * 3),
        )
        hits = reciprocal_rank_fusion(
            {"bm25": sparse, "dense": dense},
            access=access,
            rank_constant=self.rank_constant,
            limit=limit,
        )
        if rerank and self.reranker:
            return (await self.reranker.rerank(query, hits))[:limit]
        return hits
