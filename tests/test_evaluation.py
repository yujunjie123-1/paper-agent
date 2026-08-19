import pytest

from paper_agents.evaluation import EvalObservation, compare_variants


def observation(case_id: str, variant: str, success: bool) -> EvalObservation:
    return EvalObservation(
        case_id=case_id,
        variant=variant,
        task_success=success,
        blocker_defect_recall=0.8 if success else 0.4,
        citation_precision=0.9,
        tool_success=1.0,
        latency_ms=100 if variant == "single" else 150,
        total_tokens=1000 if variant == "single" else 1400,
        estimated_cost_usd=0.1 if variant == "single" else 0.14,
    )


def test_variant_report_exposes_quality_and_cost_deltas_without_declaring_winner() -> None:
    report = compare_variants(
        [
            observation("c1", "single", False),
            observation("c2", "single", True),
            observation("c1", "multi", True),
            observation("c2", "multi", True),
        ],
        dataset_version="paper-eval-v1",
        baseline_variant="single",
    )

    assert report.deltas_vs_baseline["multi"]["task_success_rate"] == 0.5
    assert report.deltas_vs_baseline["multi"]["mean_total_tokens"] == 400
    assert report.conclusion.startswith("No automatic winner")


def test_comparison_rejects_unfair_case_sets() -> None:
    with pytest.raises(ValueError, match="same case IDs"):
        compare_variants(
            [
                observation("c1", "single", True),
                observation("c2", "multi", True),
            ],
            dataset_version="v1",
            baseline_variant="single",
        )
