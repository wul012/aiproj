from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_readiness import build_release_readiness_dashboard, write_release_readiness_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT release readiness dashboard.")
    parser.add_argument("--bundle", type=Path, default=ROOT / "runs" / "release-bundle" / "release_bundle.json")
    parser.add_argument("--gate", type=Path, default=None, help="Optional gate_report.json path")
    parser.add_argument("--audit", type=Path, default=None, help="Optional project_audit.json path")
    parser.add_argument("--request-history-summary", type=Path, default=None, help="Optional request_history_summary.json path")
    parser.add_argument("--maturity", type=Path, default=None, help="Optional maturity_summary.json path")
    parser.add_argument("--ci-workflow-hygiene", type=Path, default=None, help="Optional ci_workflow_hygiene.json path")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "release-readiness")
    parser.add_argument("--title", type=str, default="MiniGPT release readiness dashboard")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_release_readiness_dashboard(
        args.bundle,
        gate_path=args.gate,
        audit_path=args.audit,
        request_history_summary_path=args.request_history_summary,
        maturity_path=args.maturity,
        ci_workflow_hygiene_path=args.ci_workflow_hygiene,
        title=args.title,
    )
    outputs = write_release_readiness_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"bundle={args.bundle}")
    print(f"readiness_status={summary.get('readiness_status')}")
    print(f"decision={summary.get('decision')}")
    print(f"release_status={summary.get('release_status')}")
    print(f"gate_status={summary.get('gate_status')}")
    print(f"audit_status={summary.get('audit_status')}")
    print(f"ci_workflow_status={summary.get('ci_workflow_status')}")
    print(f"ci_workflow_failed_checks={summary.get('ci_workflow_failed_checks')}")
    print(f"request_history_status={summary.get('request_history_status')}")
    print(f"maturity_status={summary.get('maturity_status')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report["warnings"]:
        print("warnings=" + json.dumps(report["warnings"], ensure_ascii=False))


if __name__ == "__main__":
    main()
