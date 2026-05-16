from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maturity import build_maturity_summary, write_maturity_summary_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT project maturity summary.")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=None, help="Optional registry.json path")
    parser.add_argument("--request-history-summary", type=Path, default=None, help="Optional request_history_summary.json path")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "maturity-summary")
    parser.add_argument("--title", type=str, default="MiniGPT project maturity summary")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_maturity_summary(
        args.project_root,
        registry_path=args.registry,
        request_history_summary_path=args.request_history_summary,
        title=args.title,
    )
    outputs = write_maturity_summary_outputs(summary, args.out_dir)
    overview = summary["summary"]
    print(f"project_root={summary['project_root']}")
    print(f"current_version={overview.get('current_version')}")
    print(f"overall_status={overview.get('overall_status')}")
    print(f"average_maturity_level={overview.get('average_maturity_level')}")
    print(f"release_readiness_trend_status={overview.get('release_readiness_trend_status')}")
    print(f"release_readiness_delta_count={overview.get('release_readiness_delta_count')}")
    print(f"release_readiness_regressed_count={overview.get('release_readiness_regressed_count')}")
    print(f"release_readiness_ci_workflow_regression_count={overview.get('release_readiness_ci_workflow_regression_count')}")
    print(f"release_readiness_ci_workflow_status_changed_count={overview.get('release_readiness_ci_workflow_status_changed_count')}")
    print(f"request_history_status={overview.get('request_history_status')}")
    print(f"request_history_records={overview.get('request_history_records')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
