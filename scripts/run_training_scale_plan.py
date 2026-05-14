from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_gate import POLICY_PROFILES  # noqa: E402
from minigpt.training_scale_run import run_training_scale_plan  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gate a v70 training scale plan and hand it to the portfolio batch runner.")
    parser.add_argument("--plan", type=Path, required=True, help="Path to training_scale_plan.json")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--out-root", type=Path, default=ROOT / "runs" / "training-scale-run")
    parser.add_argument("--gate-profile", choices=sorted(POLICY_PROFILES), default="review")
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--execute", action="store_true", help="Actually execute each portfolio variant. Default is dry-run.")
    parser.add_argument("--no-compare", action="store_true", help="Skip automatic batch comparison after variant reports.")
    parser.add_argument("--no-allow-warn", action="store_true", help="Block when the gate status is warn.")
    parser.add_argument("--allow-fail", action="store_true", help="Allow batch handoff even when the gate fails.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_training_scale_plan(
        args.plan,
        project_root=args.project_root,
        out_root=args.out_root,
        gate_profile=args.gate_profile,
        execute=args.execute,
        compare=not args.no_compare,
        allow_warn=not args.no_allow_warn,
        allow_fail=args.allow_fail,
        python_executable=args.python,
    )
    print(f"status={report.get('status')}")
    print(f"allowed={report.get('allowed')}")
    print(f"gate_status={report.get('gate', {}).get('overall_status')}")
    print(f"gate_profile={report.get('gate_profile')}")
    print(f"execute={report.get('execute')}")
    print("scale_plan_summary=" + json.dumps(report.get("scale_plan_summary", {}), ensure_ascii=False))
    print("gate_outputs=" + json.dumps(report.get("gate_outputs", {}), ensure_ascii=False))
    print("batch_outputs=" + json.dumps(report.get("batch_outputs", {}), ensure_ascii=False))
    print(f"run_json={Path(args.out_root) / 'training_scale_run.json'}")
    if report.get("status") in {"blocked", "failed"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
