---
name: research-design
description: Turn a research topic into a falsifiable, reproducible study and audit experiment or analysis artifacts. Use for hypotheses, preregistration, variables and controls, baselines, ablations, statistical plans, execution logs, robustness tests, or reproducibility checks.
---

# Research Design

1. State the research question, unit of analysis, falsifiable hypothesis, null/alternative, and claim boundary.
2. Define primary and secondary outcomes before seeing results. Specify variables, controls, baselines, ablations, confounders, exclusion rules, and stopping conditions.
3. Justify sample size or workload size. Select effect sizes, uncertainty intervals, and statistical tests that match the data-generating process.
4. Separate confirmatory analyses from exploratory analyses. Label post-hoc changes and preserve the original protocol.
5. Define data provenance, licenses, privacy/ethics requirements, compute budget, random seeds, dependency lock, and artifact naming.
6. Add negative controls, stress tests, leakage checks, robustness checks, and failure criteria.
7. Require human approval before costly compute, external writes, sensitive data use, or physical experiments.
8. During execution, record configuration, environment, commit, inputs, raw outputs, logs, timing, failures, and hashes. Never hide unsuccessful trials.
9. Reproduce the key result from a clean environment. Treat a failed reproduction as a result, not an inconvenience to edit away.
10. Map every reported number and figure to one immutable result artifact.

Return a protocol with: hypotheses; outcomes; datasets; baselines; controls; method; sample-size rationale; statistical plan; robustness; ethics; compute budget; stopping rule; risks; and artifact contract.

