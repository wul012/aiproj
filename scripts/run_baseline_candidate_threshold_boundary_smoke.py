from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from minigpt.baseline_candidate_threshold_boundary_smoke import (  # noqa: E402
    build_baseline_candidate_threshold_boundary_smoke_summary,
    render_baseline_candidate_threshold_boundary_smoke_text,
    write_baseline_candidate_threshold_boundary_smoke_outputs,
)
from minigpt.baseline_candidate_threshold_matrix import (  # noqa: E402
    build_baseline_candidate_threshold_matrix,
    parse_thresholds,
    write_baseline_candidate_threshold_matrix_outputs,
)
from minigpt.baseline_candidate_eval_loop import resolve_baseline_candidate_eval_loop_smoke_summary  # noqa: E402
from scripts.run_baseline_candidate_eval_loop import build_smoke_command  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a live tiny smoke and then build a baseline-candidate threshold boundary matrix.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "baseline-candidate-threshold-boundary-smoke")
    parser.add_argument(
        "--smoke-summary",
        type=Path,
        help="Reuse an existing tiny_scorecard_comparison_smoke_summary.json instead of rerunning the live smoke.",
    )
    parser.add_argument("--thresholds", default="0:1:0.5", help="Comma-separated deltas or inclusive start:stop:step range.")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
    parser.add_argument("--case-token-cap", type=int, default=3)
    parser.add_argument("--baseline-max-iters", type=int, default=1)
    parser.add_argument("--candidate-max-iters", type=int, default=2)
    parser.add_argument("--decision-min-rubric-score", type=float, default=60.0)
    parser.add_argument("--eval-iters", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=8)
    parser.add_argument("--baseline-seed", type=int, default=1337)
    parser.add_argument("--candidate-seed", type=int, default=2026)
    parser.add_argument("--require-boundary-pass", action="store_true", help="Exit with 2 unless the threshold boundary summary passes.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    protected_path = resolve_baseline_candidate_eval_loop_smoke_summary(args.smoke_summary) if args.smoke_summary else None
    prepare_output_dir(args.out_dir, force=args.force, protected_path=protected_path)
    smoke_dir = args.out_dir / "tiny-scorecard-comparison-smoke"
    check_dir = args.out_dir / "tiny-scorecard-comparison-smoke-check"
    matrix_dir = args.out_dir / "threshold-boundary-matrix"
    summary_dir = args.out_dir / "live-boundary-summary"
    logs_dir = args.out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if protected_path:
        source_mode = "reuse_summary"
        smoke_summary_path, smoke_result = reuse_smoke_summary(protected_path)
    else:
        source_mode = "rerun_smoke"
        smoke_summary_path, smoke_result = run_live_smoke(args, smoke_dir=smoke_dir, check_dir=check_dir, logs_dir=logs_dir)
    matrix_report: dict[str, Any] | None = None
    matrix_outputs: dict[str, str] | None = None
    if int(smoke_result.get("returncode") or 0) == 0 and smoke_summary_path.is_file():
        matrix_report = build_baseline_candidate_threshold_matrix(
            smoke_summary_path,
            matrix_dir,
            thresholds=parse_thresholds(args.thresholds),
        )
        matrix_outputs = write_baseline_candidate_threshold_matrix_outputs(matrix_report, matrix_dir)

    summary = build_baseline_candidate_threshold_boundary_smoke_summary(
        smoke_summary_path=smoke_summary_path,
        smoke_result=smoke_result,
        matrix_report=matrix_report,
        matrix_outputs=matrix_outputs,
        source_mode=source_mode,
    )
    outputs = write_baseline_candidate_threshold_boundary_smoke_outputs(summary, summary_dir)
    print(render_baseline_candidate_threshold_boundary_smoke_text(summary), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    exit_code = resolve_exit_code(summary, require_boundary_pass=args.require_boundary_pass)
    if exit_code:
        raise SystemExit(exit_code)


def prepare_output_dir(out_dir: Path, *, force: bool, protected_path: Path | None = None) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        if protected_path and _is_relative_to(protected_path.resolve(), out_dir.resolve()):
            raise SystemExit(f"refusing to delete output directory that contains --smoke-summary: {protected_path}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def run_live_smoke(args: argparse.Namespace, *, smoke_dir: Path, check_dir: Path, logs_dir: Path) -> tuple[Path, dict[str, Any]]:
    command = build_smoke_command(args, smoke_dir, check_dir)
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    stdout_path = logs_dir / "tiny_scorecard_comparison_smoke_stdout.txt"
    stderr_path = logs_dir / "tiny_scorecard_comparison_smoke_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return smoke_dir / "tiny_scorecard_comparison_smoke_summary.json", {
        "name": "tiny_scorecard_comparison_smoke",
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "command": command,
        "command_text": " ".join(command),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }


def reuse_smoke_summary(summary_path: Path) -> tuple[Path, dict[str, Any]]:
    return summary_path, {
        "name": "existing_tiny_scorecard_comparison_smoke_summary",
        "status": "pass",
        "returncode": 0,
        "source_summary": str(summary_path),
        "command": [],
        "command_text": "",
        "stdout": "",
        "stderr": "",
    }


def resolve_exit_code(report: dict[str, Any], *, require_boundary_pass: bool) -> int:
    if report.get("status") != "pass":
        return 1
    boundary = report.get("threshold_boundary")
    if require_boundary_pass and (not isinstance(boundary, dict) or boundary.get("status") != "pass"):
        return 2
    return 0


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
