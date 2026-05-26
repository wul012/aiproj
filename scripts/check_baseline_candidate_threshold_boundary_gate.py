from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.baseline_candidate_eval_loop import resolve_baseline_candidate_eval_loop_smoke_summary  # noqa: E402
from minigpt.baseline_candidate_threshold_boundary_gate_check import (  # noqa: E402
    build_threshold_boundary_gate_check,
    render_threshold_boundary_gate_check_text,
    write_threshold_boundary_gate_check_outputs,
)
from minigpt.baseline_candidate_threshold_boundary_smoke import BOUNDARY_SMOKE_JSON_FILENAME  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and verify a baseline-candidate threshold boundary gate expected exit.")
    parser.add_argument("--smoke-summary", type=Path, required=True, help="Existing tiny_scorecard_comparison_smoke_summary.json.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "baseline-candidate-threshold-boundary-gate-check")
    parser.add_argument("--thresholds", default="0:1:0.5")
    parser.add_argument("--expected-exit-code", type=int, default=2)
    parser.add_argument("--expected-diagnosis-decision", default="candidate_not_accepted")
    parser.add_argument("--require-boundary-pass", action="store_true")
    parser.add_argument("--require-diagnosis-pass", action="store_true")
    parser.add_argument("--require-pass", action="store_true", help="Exit 1 when the expected-exit check fails.")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    summary_path = resolve_baseline_candidate_eval_loop_smoke_summary(args.smoke_summary)
    prepare_output_dir(args.out_dir, force=args.force, protected_path=summary_path)
    run_dir = args.out_dir / "threshold-boundary-smoke"
    check_dir = args.out_dir / "gate-check"
    logs_dir = args.out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    command = build_runner_command(args, summary_path, run_dir)
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    stdout_path = logs_dir / "threshold_boundary_gate_stdout.txt"
    stderr_path = logs_dir / "threshold_boundary_gate_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    boundary_summary_path = run_dir / "live-boundary-summary" / BOUNDARY_SMOKE_JSON_FILENAME
    report = build_threshold_boundary_gate_check(
        boundary_summary_path,
        actual_exit_code=completed.returncode,
        expected_exit_code=args.expected_exit_code,
        expected_diagnosis_decision=args.expected_diagnosis_decision,
        command_text=" ".join(command),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )
    outputs = write_threshold_boundary_gate_check_outputs(report, check_dir)
    print(render_threshold_boundary_gate_check_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.require_pass and report.get("status") != "pass":
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool, protected_path: Path) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        if _is_relative_to(protected_path.resolve(), out_dir.resolve()):
            raise SystemExit(f"refusing to delete output directory that contains --smoke-summary: {protected_path}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def build_runner_command(args: argparse.Namespace, summary_path: Path, run_dir: Path) -> list[str]:
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_baseline_candidate_threshold_boundary_smoke.py"),
        "--smoke-summary",
        str(summary_path),
        "--out-dir",
        str(run_dir),
        "--thresholds",
        str(args.thresholds),
        "--force",
    ]
    if args.require_boundary_pass:
        command.append("--require-boundary-pass")
    if args.require_diagnosis_pass:
        command.append("--require-diagnosis-pass")
    return command


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
