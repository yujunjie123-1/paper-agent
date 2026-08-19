from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field


class EvalObservation(BaseModel):
    case_id: str
    variant: str
    task_success: bool
    blocker_defect_recall: float = Field(ge=0, le=1)
    citation_precision: float = Field(ge=0, le=1)
    tool_success: float = Field(ge=0, le=1)
    latency_ms: float = Field(ge=0)
    total_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    acl_leakage: bool = False
    duplicate_side_effect: bool = False


class VariantSummary(BaseModel):
    variant: str
    cases: int
    task_success_rate: float
    blocker_defect_recall: float
    citation_precision: float
    tool_success: float
    mean_latency_ms: float
    mean_total_tokens: float
    mean_estimated_cost_usd: float
    acl_leakage_count: int
    duplicate_side_effect_count: int
    releasable: bool


class ComparisonReport(BaseModel):
    dataset_version: str
    baseline_variant: str
    summaries: list[VariantSummary]
    deltas_vs_baseline: dict[str, dict[str, float]]
    conclusion: str


def summarize_variant(
    variant: str, observations: list[EvalObservation]
) -> VariantSummary:
    if not observations:
        raise ValueError(f"Variant {variant} has no observations")
    count = len(observations)

    def mean(values: list[float]) -> float:
        return sum(values) / count

    acl_leakage = sum(item.acl_leakage for item in observations)
    duplicate_side_effect = sum(item.duplicate_side_effect for item in observations)
    return VariantSummary(
        variant=variant,
        cases=count,
        task_success_rate=mean([float(item.task_success) for item in observations]),
        blocker_defect_recall=mean(
            [item.blocker_defect_recall for item in observations]
        ),
        citation_precision=mean([item.citation_precision for item in observations]),
        tool_success=mean([item.tool_success for item in observations]),
        mean_latency_ms=mean([item.latency_ms for item in observations]),
        mean_total_tokens=mean([float(item.total_tokens) for item in observations]),
        mean_estimated_cost_usd=mean(
            [item.estimated_cost_usd for item in observations]
        ),
        acl_leakage_count=acl_leakage,
        duplicate_side_effect_count=duplicate_side_effect,
        releasable=acl_leakage == 0 and duplicate_side_effect == 0,
    )


def compare_variants(
    observations: list[EvalObservation],
    *,
    dataset_version: str,
    baseline_variant: str,
) -> ComparisonReport:
    grouped: defaultdict[str, list[EvalObservation]] = defaultdict(list)
    case_sets: defaultdict[str, set[str]] = defaultdict(set)
    for observation in observations:
        grouped[observation.variant].append(observation)
        case_sets[observation.variant].add(observation.case_id)
    if baseline_variant not in grouped:
        raise ValueError(f"Missing baseline variant: {baseline_variant}")
    baseline_cases = case_sets[baseline_variant]
    mismatched = {
        variant: sorted(cases ^ baseline_cases)
        for variant, cases in case_sets.items()
        if cases != baseline_cases
    }
    if mismatched:
        raise ValueError(f"Variants must use the same case IDs: {mismatched}")

    summaries = [summarize_variant(name, grouped[name]) for name in sorted(grouped)]
    by_name = {summary.variant: summary for summary in summaries}
    baseline = by_name[baseline_variant]
    deltas: dict[str, dict[str, float]] = {}
    for variant, summary in by_name.items():
        if variant == baseline_variant:
            continue
        deltas[variant] = {
            "task_success_rate": summary.task_success_rate
            - baseline.task_success_rate,
            "blocker_defect_recall": summary.blocker_defect_recall
            - baseline.blocker_defect_recall,
            "citation_precision": summary.citation_precision
            - baseline.citation_precision,
            "mean_latency_ms": summary.mean_latency_ms - baseline.mean_latency_ms,
            "mean_total_tokens": summary.mean_total_tokens
            - baseline.mean_total_tokens,
            "mean_estimated_cost_usd": summary.mean_estimated_cost_usd
            - baseline.mean_estimated_cost_usd,
        }
    return ComparisonReport(
        dataset_version=dataset_version,
        baseline_variant=baseline_variant,
        summaries=summaries,
        deltas_vs_baseline=deltas,
        conclusion=(
            "No automatic winner: inspect quality deltas, guardrails, uncertainty, "
            "latency and cost before a human release decision."
        ),
    )
