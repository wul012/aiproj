from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_run_evidence import build_training_run_evidence, write_training_run_evidence_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build evidence reports for a real MiniGPT training run directory.")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to <run-dir>/training-run-evidence")
    parser.add_argument("--title", type=str, default="MiniGPT training run evidence")
    parser.add_argument("--require-sample", action="store_true", help="Treat missing sample.txt as a blocking issue.")
    parser.add_argument("--require-eval-suite", action="store_true", help="Treat missing eval suite output as a blocking issue.")
    parser.add_argument("--fail-on-blocked", action="store_true", help="Exit non-zero when the evidence status is blocked.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.run_dir / "training-run-evidence"
    report = build_training_run_evidence(
        args.run_dir,
        title=args.title,
        require_sample=args.require_sample,
        require_eval_suite=args.require_eval_suite,
    )
    outputs = write_training_run_evidence_outputs(report, out_dir)
    summary = report["summary"]
    print(f"run_dir={report['run_dir']}")
    print(f"status={summary.get('status')}")
    print(f"readiness_score={summary.get('readiness_score')}")
    print(f"core_artifacts={summary.get('core_available_count')}/{summary.get('core_artifact_count')}")
    print(f"artifacts={summary.get('available_artifact_count')}/{summary.get('artifact_count')}")
    print(f"critical_missing_count={summary.get('critical_missing_count')}")
    print(f"warning_count={summary.get('warning_count')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.fail_on_blocked and summary.get("status") == "blocked":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
