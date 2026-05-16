from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.ci_workflow_hygiene import build_ci_workflow_hygiene_report, write_ci_workflow_hygiene_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MiniGPT CI workflow hygiene.")
    parser.add_argument("--workflow", type=Path, default=ROOT / ".github" / "workflows" / "ci.yml")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "ci-workflow-hygiene")
    parser.add_argument("--title", type=str, default="MiniGPT CI workflow hygiene")
    parser.add_argument("--no-fail", action="store_true", help="Write the report without returning a non-zero status.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_ci_workflow_hygiene_report(args.workflow, project_root=ROOT, title=args.title)
    outputs = write_ci_workflow_hygiene_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={summary['status']}")
    print(f"decision={summary['decision']}")
    print(f"check_count={summary['check_count']}")
    print(f"passed_check_count={summary['passed_check_count']}")
    print(f"failed_check_count={summary['failed_check_count']}")
    print(f"action_count={summary['action_count']}")
    print(f"node24_native_action_count={summary['node24_native_action_count']}")
    print(f"forbidden_env_count={summary['forbidden_env_count']}")
    print(f"missing_step_count={summary['missing_step_count']}")
    print(f"python_version={summary['python_version']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if summary["status"] != "pass" and not args.no_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
