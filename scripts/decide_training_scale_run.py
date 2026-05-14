from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_run_decision import (  # noqa: E402
    build_training_scale_run_decision,
    write_training_scale_run_decision_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Choose the safest MiniGPT gated training scale run to execute next.")
    parser.add_argument("comparison", type=Path, help="training_scale_run_comparison.json file or comparison directory")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "training-scale-run-decision")
    parser.add_argument("--min-readiness", type=int, default=60)
    parser.add_argument("--require-gate-pass", action="store_true", help="Reject warn-status gate runs.")
    parser.add_argument("--no-require-batch-started", action="store_true", help="Allow candidates that did not reach batch dry-run.")
    parser.add_argument("--execute-out-root", type=Path, default=None, help="Output directory for the generated --execute command.")
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--title", type=str, default="MiniGPT training scale run decision")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_training_scale_run_decision(
        args.comparison,
        min_readiness=args.min_readiness,
        require_gate_pass=args.require_gate_pass,
        require_batch_started=not args.no_require_batch_started,
        execute_out_root=args.execute_out_root,
        python_executable=args.python,
        title=args.title,
    )
    outputs = write_training_scale_run_decision_outputs(report, args.out_dir)
    print(f"decision_status={report.get('decision_status')}")
    print(f"recommended_action={report.get('recommended_action')}")
    print("selected_run=" + json.dumps(report.get("selected_run", {}), ensure_ascii=False))
    print("summary=" + json.dumps(report.get("summary", {}), ensure_ascii=False))
    print(f"execute_command={report.get('execute_command_text')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report.get("decision_status") == "blocked":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
