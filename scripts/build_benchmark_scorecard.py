from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.benchmark_scorecard import build_benchmark_scorecard, write_benchmark_scorecard_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a consolidated MiniGPT benchmark scorecard for one run.")
    parser.add_argument("--run-dir", type=Path, required=True, help="Run directory containing eval/pair/quality evidence")
    parser.add_argument("--registry", type=Path, default=None, help="Optional registry.json path for cross-run context")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to <run-dir>/benchmark-scorecard")
    parser.add_argument("--title", type=str, default="MiniGPT benchmark scorecard")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.run_dir / "benchmark-scorecard"
    scorecard = build_benchmark_scorecard(args.run_dir, registry_path=args.registry, title=args.title)
    outputs = write_benchmark_scorecard_outputs(scorecard, out_dir)
    summary = scorecard["summary"]
    print(f"run_dir={scorecard['run_dir']}")
    print(f"overall_status={summary.get('overall_status')}")
    print(f"overall_score={summary.get('overall_score')}")
    print(f"component_count={summary.get('component_count')}")
    print(f"case_score_count={len(scorecard.get('case_scores', []))}")
    print(f"rubric_status={summary.get('rubric_status')}")
    print(f"rubric_avg_score={summary.get('rubric_avg_score')}")
    print(f"weakest_rubric_case={summary.get('weakest_rubric_case')}")
    print(f"task_type_group_count={summary.get('task_type_group_count')}")
    print(f"weakest_task_type={summary.get('weakest_task_type')}")
    print(f"difficulty_group_count={summary.get('difficulty_group_count')}")
    print(f"weakest_difficulty={summary.get('weakest_difficulty')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
