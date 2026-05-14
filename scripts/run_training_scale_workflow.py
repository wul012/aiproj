from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_gate import POLICY_PROFILES  # noqa: E402
from minigpt.training_scale_workflow import run_training_scale_workflow  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the consolidated MiniGPT training scale workflow.")
    parser.add_argument("sources", nargs="+", type=Path, help="Training text files or directories")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--out-root", type=Path, default=ROOT / "runs" / "training-scale-workflow")
    parser.add_argument("--profile", action="append", choices=sorted(POLICY_PROFILES), default=None, help="Gate profile to include; repeat to compare profiles.")
    parser.add_argument("--baseline-profile", type=str, default=None, help="Baseline profile for comparison. Defaults to the first profile.")
    parser.add_argument("--dataset-name", type=str, default="portfolio-zh")
    parser.add_argument("--dataset-version-prefix", type=str, default="v75")
    parser.add_argument("--dataset-description", type=str, default="MiniGPT corpus planned for scale-aware training.")
    parser.add_argument("--max-variants", type=int, default=3)
    parser.add_argument("--sample-prompt", type=str, default="MiniGPT")
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--execute", action="store_true", help="Actually execute the profile batch runs. Default is dry-run.")
    parser.add_argument("--no-compare", action="store_true", help="Skip per-profile portfolio comparison after variant reports.")
    parser.add_argument("--no-allow-warn", action="store_true", help="Block warn-status gated runs.")
    parser.add_argument("--allow-fail", action="store_true", help="Allow failed gates to reach batch handoff.")
    parser.add_argument("--decision-min-readiness", type=int, default=60)
    parser.add_argument("--decision-require-gate-pass", action="store_true", help="Only let pass-status gates become decision candidates.")
    parser.add_argument("--decision-no-require-batch-started", action="store_true", help="Allow decision candidates that did not reach batch dry-run.")
    parser.add_argument("--decision-execute-out-root", type=Path, default=None)
    parser.add_argument("--title", type=str, default="MiniGPT training scale workflow")
    parser.add_argument("--no-recursive", action="store_true", help="Only read top-level .txt files from directories.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_training_scale_workflow(
        args.sources,
        project_root=args.project_root,
        out_root=args.out_root,
        profiles=args.profile,
        baseline_profile=args.baseline_profile,
        dataset_name=args.dataset_name,
        dataset_version_prefix=args.dataset_version_prefix,
        dataset_description=args.dataset_description,
        recursive=not args.no_recursive,
        max_variants=args.max_variants,
        sample_prompt=args.sample_prompt,
        execute=args.execute,
        compare=not args.no_compare,
        allow_warn=not args.no_allow_warn,
        allow_fail=args.allow_fail,
        decision_min_readiness=args.decision_min_readiness,
        decision_require_gate_pass=args.decision_require_gate_pass,
        decision_require_batch_started=not args.decision_no_require_batch_started,
        decision_execute_out_root=args.decision_execute_out_root,
        python_executable=args.python,
        title=args.title,
    )
    print(f"workflow_status={report.get('summary', {}).get('decision_status')}")
    print(f"recommended_action={report.get('summary', {}).get('recommended_action')}")
    print(f"selected_profile={report.get('summary', {}).get('selected_profile')}")
    print(f"scale_tier={report.get('summary', {}).get('scale_tier')}")
    print(f"profiles={','.join(report.get('profiles', []))}")
    print("summary=" + json.dumps(report.get("summary", {}), ensure_ascii=False))
    print(f"execute_command={report.get('execute_command_text')}")
    print(
        "outputs="
        + json.dumps(
            {
                "json": str(Path(args.out_root) / "training_scale_workflow.json"),
                "csv": str(Path(args.out_root) / "training_scale_workflow.csv"),
                "markdown": str(Path(args.out_root) / "training_scale_workflow.md"),
                "html": str(Path(args.out_root) / "training_scale_workflow.html"),
                "plan": report.get("plan_outputs", {}).get("json"),
                "comparison": report.get("comparison_outputs", {}).get("json"),
                "decision": report.get("decision_outputs", {}).get("json"),
            },
            ensure_ascii=False,
        )
    )
    if report.get("summary", {}).get("decision_status") == "blocked":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
