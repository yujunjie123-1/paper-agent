---
name: evidence-ledger
description: Search, screen, deduplicate, verify, and synthesize scholarly evidence into a claim-level ledger. Use for literature reviews, prior-art and novelty checks, citation graph expansion, systematic search logs, citation verification, or grounding manuscript claims.
---

# Evidence Ledger

1. Translate the research question into concepts, synonyms, exclusions, date bounds, and database-specific query strings.
2. Run complementary lanes: semantic/keyword search, backward citations, forward citations, and an adversarial lane for contradictions, negative results, and failed replications.
3. Log database, exact query, timestamp, filters, and result count. Do not silently change screening criteria.
4. Deduplicate by DOI first, then stable identifier, then normalized title plus year.
5. Screen title/abstract before full text. Record inclusion and exclusion reasons.
6. Distinguish peer-reviewed articles, accepted manuscripts, preprints, datasets, software, editorials, and retractions.
7. Verify title, authors, venue, year, DOI/URL, and publication status against a primary registry or publisher page. Never cite a search snippet.
8. Extract claims at atomic granularity. Link each claim to supporting, contradicting, or contextual evidence and the exact page/section when available.
9. Score evidence quality separately from relevance. Preserve disagreement instead of averaging it away.
10. Quarantine unverifiable references; never create a plausible-looking citation.

Return records shaped like:

```json
{
  "work_id": "doi or stable id",
  "bibliography": {},
  "publication_status": "peer-reviewed|preprint|other",
  "source_url": "...",
  "claims": [{"text": "...", "relation": "supports|contradicts|context", "locator": "..."}],
  "quality": 0.0,
  "relevance": 0.0,
  "verification": "verified|partial|quarantined"
}
```

Report coverage limits, database blind spots, language bias, unavailable full text, and the date after which the search is stale.

