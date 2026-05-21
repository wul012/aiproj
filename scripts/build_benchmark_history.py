from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.benchmark_history import build_benchmark_history, write_benchmark_history_outputs  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT benchmark scorecard history ledger.")
    parser.add_argument("comparisons", nargs="+", type=Path, help="benchmark_scorecard_comparison.json files or output directories")
    parser.add_argument("--decisions", nargs="*", type=Path, default=None, help="Optional matching benchmark_scorecard_decision.json files or directories")
    parser.add_argument("--names", nargs="*", default=None, help="Optional names matching comparisons")
    parser.add_argument("--evidence-kind", choices=["real-benchmark", "tiny-smoke"], default="real-benchmark")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "benchmark-history")
    parser.add_argument("--title", type=str, default="MiniGPT benchmark history")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_benchmark_history(
        args.comparisons,
        decision_paths=args.decisions,
        names=args.names,
        evidence_kind=args.evidence_kind,
        title=args.title,
    )
    outputs = write_benchmark_history_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"entry_count={summary['entry_count']}")
    print(f"promote_count={summary['promote_count']}")
    print(f"review_count={summary['review_count']}")
    print(f"blocked_count={summary['blocked_count']}")
    print(f"ready_count={summary['ready_count']}")
    print(f"model_quality_claim={summary['model_quality_claim']}")
    print(f"best_candidate_name={summary['best_candidate_name']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
