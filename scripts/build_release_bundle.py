from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_bundle import build_release_bundle, write_release_bundle_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT release evidence bundle.")
    parser.add_argument("--registry", type=Path, default=ROOT / "runs" / "registry" / "registry.json")
    parser.add_argument("--model-card", type=Path, default=None, help="Optional model_card.json path")
    parser.add_argument("--audit", type=Path, default=None, help="Optional project_audit.json path")
    parser.add_argument("--request-history-summary", type=Path, default=None, help="Optional request_history_summary.json path")
    parser.add_argument("--ci-workflow-hygiene", type=Path, default=None, help="Optional ci_workflow_hygiene.json path")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to runs/release-bundle")
    parser.add_argument("--release-name", type=str, default=None)
    parser.add_argument("--title", type=str, default="MiniGPT release bundle")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.registry.parent.parent / "release-bundle"
    bundle = build_release_bundle(
        args.registry,
        model_card_path=args.model_card,
        audit_path=args.audit,
        request_history_summary_path=args.request_history_summary,
        ci_workflow_hygiene_path=args.ci_workflow_hygiene,
        release_name=args.release_name,
        title=args.title,
    )
    outputs = write_release_bundle_outputs(bundle, out_dir)
    summary = bundle["summary"]

    print(f"registry={args.registry}")
    print(f"release_status={summary['release_status']}")
    print(f"audit_status={summary['audit_status']}")
    print(f"request_history_status={summary.get('request_history_status')}")
    print(f"ci_workflow_status={summary.get('ci_workflow_status')}")
    print(f"ci_workflow_failed_checks={summary.get('ci_workflow_failed_checks')}")
    print(f"best_run={summary['best_run_name']}")
    print(f"artifacts={summary['available_artifacts']} available/{summary['missing_artifacts']} missing")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if bundle["warnings"]:
        print("warnings=" + json.dumps(bundle["warnings"], ensure_ascii=False))


if __name__ == "__main__":
    main()
