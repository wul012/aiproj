from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.baseline_candidate_threshold_matrix import (  # noqa: E402
    build_baseline_candidate_threshold_matrix,
    parse_thresholds,
    render_baseline_candidate_threshold_matrix_text,
    write_baseline_candidate_threshold_matrix_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a MiniGPT baseline-candidate threshold matrix from one smoke summary.")
    parser.add_argument("smoke_summary", type=Path, help="Path to tiny_scorecard_comparison_smoke_summary.json or its directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "baseline-candidate-threshold-matrix")
    parser.add_argument("--thresholds", default="0:1:0.5", help="Comma-separated deltas or inclusive start:stop:step range.")
    parser.add_argument("--require-both-outcomes", action="store_true", help="Exit with 2 unless the matrix has accept and reject rows.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_baseline_candidate_threshold_matrix(
        args.smoke_summary,
        args.out_dir,
        thresholds=parse_thresholds(args.thresholds),
    )
    outputs = write_baseline_candidate_threshold_matrix_outputs(report, args.out_dir)
    print(render_baseline_candidate_threshold_matrix_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    exit_code = resolve_exit_code(report, require_both_outcomes=args.require_both_outcomes)
    if exit_code:
        raise SystemExit(exit_code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def resolve_exit_code(report: dict[str, Any], *, require_both_outcomes: bool) -> int:
    if report.get("status") != "pass":
        return 1
    if require_both_outcomes and (int(report.get("accept_count") or 0) < 1 or int(report.get("reject_count") or 0) < 1):
        return 2
    return 0


if __name__ == "__main__":
    main()
