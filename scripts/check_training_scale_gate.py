from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_gate import (  # noqa: E402
    POLICY_PROFILES,
    build_training_scale_gate,
    load_training_scale_plan,
    write_training_scale_gate_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether a MiniGPT training scale plan is ready to execute.")
    parser.add_argument("--plan", type=Path, required=True, help="Path to training_scale_plan.json")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "training-scale-gate")
    parser.add_argument("--profile", choices=sorted(POLICY_PROFILES), default="review")
    parser.add_argument("--title", type=str, default="MiniGPT training scale gate")
    parser.add_argument("--no-fail", action="store_true", help="Write gate outputs but do not exit non-zero on fail.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan = load_training_scale_plan(args.plan)
    report = build_training_scale_gate(plan, plan_path=args.plan, profile=args.profile, title=args.title)
    outputs = write_training_scale_gate_outputs(report, args.out_dir)
    print(f"status={report.get('overall_status')}")
    print(f"profile={report.get('profile')}")
    print(f"pass_count={report.get('pass_count')}")
    print(f"warn_count={report.get('warn_count')}")
    print(f"fail_count={report.get('fail_count')}")
    print("plan_summary=" + json.dumps(report.get("plan_summary", {}), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report.get("overall_status") == "fail" and not args.no_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
