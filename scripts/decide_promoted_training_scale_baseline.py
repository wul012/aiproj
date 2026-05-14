from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_decision import (  # noqa: E402
    build_promoted_training_scale_decision,
    write_promoted_training_scale_decision_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select the next MiniGPT baseline from a promoted training scale comparison.")
    parser.add_argument("comparison", type=Path, help="promoted_training_scale_comparison.json file or comparison directory")
    parser.add_argument("--min-readiness", type=int, default=70)
    parser.add_argument("--require-gate-pass", action="store_true")
    parser.add_argument("--allow-incomplete-batch", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "promoted-training-scale-decision")
    parser.add_argument("--title", type=str, default="MiniGPT promoted training scale baseline decision")
    parser.add_argument("--require-accepted", action="store_true", help="Exit non-zero unless the selected baseline is accepted")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_promoted_training_scale_decision(
        args.comparison,
        min_readiness=args.min_readiness,
        require_gate_pass=args.require_gate_pass,
        require_batch_completed=not args.allow_incomplete_batch,
        title=args.title,
    )
    outputs = write_promoted_training_scale_decision_outputs(report, args.out_dir)
    summary = report["summary"]
    selected = report.get("selected_baseline") or {}
    print(f"decision_status={report['decision_status']}")
    print(f"selected_baseline={selected.get('name')}")
    print(f"selected_readiness={selected.get('readiness_score')}")
    print(f"candidate_count={summary.get('candidate_count')}")
    print(f"rejected_count={summary.get('rejected_count')}")
    print("summary=" + json.dumps(summary, ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.require_accepted and report["decision_status"] != "accepted":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
