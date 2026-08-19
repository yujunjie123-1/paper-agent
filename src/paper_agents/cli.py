from __future__ import annotations

import argparse
import asyncio
import json

from .models import ApprovalRequest, ResearchBrief
from .orchestrator import PaperOrchestrator


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paper-agents")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the standard research lifecycle")
    run.add_argument("--auto-approve", action="store_true")

    legacy = subparsers.add_parser("demo", help=argparse.SUPPRESS)
    legacy.add_argument("--auto-approve", action="store_true")

    show = subparsers.add_parser("show", help="Show a persisted run")
    show.add_argument("run_id")

    approve = subparsers.add_parser("approve", help="Approve a pending human gate")
    approve.add_argument("run_id")
    approve.add_argument("gate", choices=["research_plan", "submission"])
    approve.add_argument("--note", default="approved from CLI")
    return parser


async def _run(args: argparse.Namespace) -> None:
    orchestrator = PaperOrchestrator()
    if args.command in {"run", "demo"}:
        state = await orchestrator.start(
            ResearchBrief(
                goal="构建并评测一个可恢复、评审驱动的论文多智能体系统",
                domain="AI Agent Engineering",
                candidate_venues=["journal", "conference", "competition"],
                constraints={"validation_mode": "local", "no_fabricated_metrics": True},
                auto_approve=args.auto_approve,
            )
        )
    elif args.command == "show":
        state = orchestrator.get_run(args.run_id)
    else:
        pending = orchestrator.get_run(args.run_id)
        state = await orchestrator.approve(
            args.run_id,
            args.gate,
            ApprovalRequest(
                decision="approve",
                note=args.note,
                reviewer="cli-user",
                artifact_sha256s=orchestrator.expected_gate_hashes(pending, args.gate),
            ),
        )
    print(json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2))


def main() -> None:
    asyncio.run(_run(_parser().parse_args()))


if __name__ == "__main__":
    main()
