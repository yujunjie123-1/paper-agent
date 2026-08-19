# Academic References and Benchmarks

This list is a practical reference set for designing, evaluating, and positioning a research-oriented multi-agent system. Each entry links to an official venue, challenge, or publisher page and identifies the repository artifact it informs.

## Competitions and benchmark programs

| Venue or program | Official page | Relevance to paper-agent |
| --- | --- | --- |
| NeurIPS Competitions | https://neurips.cc/Competitions | Challenge-style task definitions, fixed evaluation protocols, and reproducible submissions. |
| KDD Cup | https://www.kdd.org/kdd-cup | Applied data-mining competition structure and leaderboard-oriented evaluation. |
| TREC | https://trec.nist.gov/ | Information-retrieval test collections, relevance judgments, and Recall/MRR/NDCG-style reporting. |
| BioASQ | https://bioasq.org/ | Biomedical semantic indexing and question-answering tasks with evidence-grounded answers. |
| SemEval | https://semeval.github.io/ | Shared-task design for NLP evaluation, annotation guidelines, and comparable system reports. |
| NeurIPS Datasets and Benchmarks | https://neurips.cc/Conferences/2024/CallForDatasetsBenchmarks | Dataset cards, benchmark documentation, limitations, and transparent evaluation reporting. |

## Journals and publication venues

| Venue | Official page | How it informs the project |
| --- | --- | --- |
| AIChE Journal | https://aiche.onlinelibrary.wiley.com/journal/15475905 | Chemical-engineering research framing, reproducibility expectations, and process-system applications. |
| Chemical Engineering Journal | https://www.sciencedirect.com/journal/chemical-engineering-journal | High-impact chemical-engineering studies combining modeling, experiments, and engineering relevance. |
| Computers & Chemical Engineering | https://www.sciencedirect.com/journal/computers-and-chemical-engineering | Computational process engineering, optimization, simulation, and data-driven workflow references. |
| Journal of Chemical Information and Modeling | https://pubs.acs.org/journal/jcisd8 | Chemical-informatics data, molecular modeling, machine learning, and benchmark design. |
| Journal of Chemical Theory and Computation | https://pubs.acs.org/journal/jctcce | Computational chemistry methods, validation, and evidence-linked scientific claims. |
| Nature Machine Intelligence | https://www.nature.com/natmachintell/ | Machine-learning system novelty, broad impact framing, and rigorous methods reporting. |
| Patterns | https://www.cell.com/patterns/home | Data and AI research artifacts, dataset documentation, and reusable computational workflows. |
| Journal of Cheminformatics | https://jcheminf.biomedcentral.com/ | Open computational chemistry methods, software, datasets, and reproducibility practices. |
| ACM Transactions on Intelligent Systems and Technology | https://dl.acm.org/journal/tiis | Intelligent-system evaluation, human-facing workflows, and empirical system comparisons. |

## Research papers and evaluation guidance

| Resource | Link | Use in this repository |
| --- | --- | --- |
| PaperBench | https://openai.com/index/paperbench/ | Research-agent task decomposition, artifact-based grading, and end-to-end paper-building evaluation. |
| PaperWritingBench | https://arxiv.org/abs/2604.05018 | Evidence-aware scientific writing and structured pre-writing artifact design. |
| OpenAI agent evaluation guide | https://developers.openai.com/api/docs/guides/agent-evals | Trace grading, dataset versioning, and regression evaluation workflow. |

## Mapping to repository artifacts

- Venue requirements and submission checks: `skills/venue-intelligence/`, `config/agents.yaml`, and `docs/WORKFLOW.md`.
- Retrieval and evidence evaluation: `src/paper_agents/retrieval.py`, `config/retrieval.yaml`, and `tests/test_retrieval.py`.
- Agent workflow evaluation: `config/evaluation.yaml`, `src/paper_agents/evaluation.py`, and `docs/EVALUATION_PLAN.md`.
- Rebuttal and review workflow: `skills/revision-rebuttal/`, `skills/expert-review/`, and `tests/test_orchestrator.py`.

Venue scope, author instructions, and competition rules change over time. Before an actual submission, re-check the official page and archive the version used by the run.
