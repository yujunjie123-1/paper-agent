---
name: venue-intelligence
description: Verify and compare journals, conferences, workshops, calls for papers, and research competitions using official sources. Use for venue discovery, scope fit, deadline and policy checks, submission checklists, or deciding where a paper/project should be submitted.
---

# Venue Intelligence

1. Determine whether the target is a journal, conference, workshop, or competition. Keep categories separate.
2. Search broadly only to discover candidates. Treat only the venue, publisher, society, or organizer website as authoritative for requirements.
3. Capture the exact source URL, page title, quoted field, retrieval timestamp, and applicable year/version for every rule.
4. Extract scope, article/track type, eligibility, required deliverables, page/word limit, anonymity, data/code policy, ethics/AI disclosure, fees, deadlines, timezone, review model, and double-submission policy.
5. Mark missing or conflicting fields as `unknown` or `conflict`; never infer them from a previous year.
6. Take a rules snapshot because venue pages change. Require a fresh verification immediately before submission.
7. Rank candidates with declared weights: topic fit, evidence maturity, schedule feasibility, resource cost, acceptance risk, audience value, and policy compatibility.
8. Return a decision plus alternatives and disqualifying constraints. Do not equate prestige with fit.

Use this output contract:

```json
{
  "candidate": "name and year",
  "category": "journal|conference|workshop|competition",
  "verified_at": "ISO-8601",
  "official_sources": [{"field": "deadline", "url": "...", "value": "..."}],
  "fit_score": 0.0,
  "hard_constraints": [],
  "unknowns": [],
  "decision": "shortlist|reject|human-check"
}
```

Stop and request human verification when a deadline, fee, eligibility rule, legal term, or submission action cannot be confirmed from an official source.

