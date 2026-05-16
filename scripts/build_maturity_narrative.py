from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maturity_narrative import build_maturity_narrative, write_maturity_narrative_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT release-quality maturity narrative.")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--maturity", type=Path, default=None, help="Optional maturity_summary.json path")
    parser.add_argument("--registry", type=Path, default=None, help="Optional registry.json path")
    parser.add_argument(
        "--request-history-summary",
        type=Path,
        default=None,
        help="Optional request_history_summary.json path",
    )
    parser.add_argument(
        "--benchmark-scorecard",
        type=Path,
        action="append",
        default=[],
        help="Optional benchmark_scorecard.json path. Repeat for multiple scorecards.",
    )
    parser.add_argument(
        "--benchmark-scorecard-decision",
        type=Path,
        action="append",
        default=[],
        help="Optional benchmark_scorecard_decision.json path. Repeat for multiple decisions.",
    )
    parser.add_argument(
        "--dataset-card",
        type=Path,
        action="append",
        default=[],
        help="Optional dataset_card.json path. Repeat for multiple dataset cards.",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "maturity-narrative")
    parser.add_argument("--title", type=str, default="MiniGPT release-quality maturity narrative")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    narrative = build_maturity_narrative(
        args.project_root,
        maturity_path=args.maturity,
        registry_path=args.registry,
        request_history_summary_path=args.request_history_summary,
        benchmark_scorecard_paths=args.benchmark_scorecard or None,
        benchmark_scorecard_decision_paths=args.benchmark_scorecard_decision or None,
        dataset_card_paths=args.dataset_card or None,
        title=args.title,
    )
    outputs = write_maturity_narrative_outputs(narrative, args.out_dir)
    summary = narrative["summary"]
    print(f"project_root={narrative['project_root']}")
    print(f"portfolio_status={summary.get('portfolio_status')}")
    print(f"current_version={summary.get('current_version')}")
    print(f"maturity_status={summary.get('maturity_status')}")
    print(f"release_readiness_trend_status={summary.get('release_readiness_trend_status')}")
    print(f"request_history_status={summary.get('request_history_status')}")
    print(f"benchmark_scorecards={summary.get('benchmark_scorecard_count')}")
    print(f"benchmark_scorecard_decisions={summary.get('benchmark_decision_count')}")
    print(f"benchmark_decision_selected_run={summary.get('benchmark_decision_selected_run')}")
    print(f"dataset_cards={summary.get('dataset_card_count')}")
    print("warnings=" + json.dumps(narrative.get("warnings", []), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
