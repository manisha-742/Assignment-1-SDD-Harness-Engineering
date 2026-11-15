"""Command-line interface for the local reminder agent."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from reminder_agent.context import ContextConfigurationError, RuntimeContext
from reminder_agent.evaluation import (
    DATASET_PATH,
    EvaluationIntegrityError,
    EvaluationMetadataError,
    finalize_evaluation,
    run_evaluation,
    run_offline_replay,
)
from reminder_agent.interpreter import (
    ProviderConfigurationError,
    ProviderError,
    interpret_request,
)
from reminder_agent.semantic_scoring import InvalidSemanticScore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reminder-agent")
    commands = parser.add_subparsers(dest="command", required=True)
    interpret = commands.add_parser("interpret", help="interpret one reminder request")
    interpret.add_argument(
        "request", nargs="+", help="natural-language reminder request"
    )
    evaluate = commands.add_parser("evaluate", help="run the fixed evaluation dataset")
    evaluate.add_argument("--cases", type=Path, default=DATASET_PATH)
    evaluate.add_argument("--repair-of", type=Path)
    evaluate.add_argument("--repair-feedback", type=Path)
    replay = commands.add_parser("replay", help="revalidate captured outputs offline")
    replay.add_argument("--run-dir", type=Path, required=True)
    finalize = commands.add_parser("finalize", help="finalize human semantic scoring")
    finalize.add_argument("--run-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "interpret":
        request = " ".join(args.request)
        try:
            context = RuntimeContext.from_environment()
            result = interpret_request(request, context)
        except (
            ContextConfigurationError,
            ProviderConfigurationError,
            ProviderError,
        ) as error:
            print(str(error), file=sys.stderr)
            return 1
        print(json.dumps(result.to_dict(), ensure_ascii=False))
        return 0
    if args.command == "evaluate":
        try:
            run_dir = run_evaluation(
                args.cases,
                repair_of=args.repair_of,
                repair_feedback_path=args.repair_feedback,
            )
        except (
            EvaluationIntegrityError,
            EvaluationMetadataError,
            ProviderConfigurationError,
            OSError,
        ) as error:
            print(str(error), file=sys.stderr)
            return 1
        print(str(run_dir))
        return 0
    if args.command == "replay":
        try:
            run_dir = run_offline_replay(args.run_dir)
        except (EvaluationIntegrityError, OSError) as error:
            print(str(error), file=sys.stderr)
            return 1
        print(str(run_dir))
        return 0
    if args.command == "finalize":
        try:
            summary = finalize_evaluation(args.run_dir)
        except (
            InvalidSemanticScore,
            OSError,
            json.JSONDecodeError,
            ValueError,
        ) as error:
            print(str(error), file=sys.stderr)
            return 1
        print(summary["aggregate"]["status"])
        return 0
    print("Unsupported command.", file=sys.stderr)
    return 2
