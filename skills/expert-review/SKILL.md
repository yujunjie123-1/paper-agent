---
name: expert-review
description: Conduct independent, evidence-located expert review of a manuscript and its research artifacts. Use for methods, statistics, novelty, ethics, reproducibility, venue-compliance review, adversarial pre-submission review, review aggregation, or deciding whether revision is required.
---

# Expert Review

1. Review independently before seeing other reviewers' conclusions. Use only the assigned rubric dimension.
2. Separate fatal validity defects, major claim-changing defects, minor corrections, and optional notes.
3. Locate every finding in a manuscript section, claim, table, figure, equation, code path, or artifact.
4. State the evidence for the finding, the consequence if unfixed, and a testable required action.
5. Recalculate or rerun checks when tools and data permit. Say `not verifiable` when they do not.
6. Search for recent or adjacent prior art when reviewing novelty; verify sources before citing them.
7. Check whether stated limitations actually bound the claims.
8. Assign confidence independently of severity. Avoid vague comments such as “needs more detail.”
9. Do not rewrite the paper during review.
10. During aggregation, merge duplicates, preserve minority objections, identify conflicts, and adjudicate by evidence rather than majority vote.

Return each issue with `severity`, `dimension`, `location`, `finding`, `evidence`, `required_action`, and `confidence`. Return a rubric score, but never let the aggregate number hide an unresolved blocker.

