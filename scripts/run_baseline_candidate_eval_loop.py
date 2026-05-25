from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.baseline_candidate_eval_loop import (  # noqa: E402
    build_baseline_candidate_eval_loop_report,
    render_baseline_candidate_eval_loop_text,
    resolve_baseline_candidate_eval_loop_smoke_summary,
    write_baseline_candidate_eval_loop_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a reproducible MiniGPT baseline-candidate eval loop.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "baseline-candidate-eval-loop")
    parser.add_argument(
        "--smoke-summary",
        type=Path,
        help="Reuse an existing tiny scorecard comparison smoke summary JSON instead of rerunning the smoke.",
    )
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
    parser.add_argument("--case-token-cap", type=int, default=3)
    parser.add_argument("--baseline-max-iters", type=int, default=1)
    parser.add_argument("--candidate-max-iters", type=int, default=2)
    parser.add_argument("--decision-min-rubric-score", type=float, default=60.0)
    parser.add_argument("--min-overall-score-delta", type=float, default=0.0)
    parser.add_argument("--eval-iters", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=8)
    parser.add_argument("--baseline-seed", type=int, default=1337)
    parser.add_argument("--candidate-seed", type=int, default=2026)
    parser.add_argument(
        "--fail-on-reject",
        action="store_true",
        help="Exit non-zero when the loop runs successfully but rejects the candidate.",
    )
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.baseline_max_iters < 1:
        raise ValueError("--baseline-max-iters must be at least 1")
    if args.candidate_max_iters < 1:
        raise ValueError("--candidate-max-iters must be at least 1")
    out_dir = args.out_dir
    protected_path = resolve_baseline_candidate_eval_loop_smoke_summary(args.smoke_summary) if args.smoke_summary else None
    prepare_output_dir(out_dir, force=args.force, protected_path=protected_path)
    command_result: dict[str, Any]
    if protected_path:
        source_mode = "reuse_summary"
        summary_path = protected_path
        command_result = {
            "name": "existing_tiny_scorecard_comparison_smoke_summary",
            "status": "pass",
            "returncode": 0,
            "source_summary": str(summary_path),
            "command": [],
            "command_text": "",
            "stdout": "",
            "stderr": "",
        }
    else:
        source_mode = "rerun_smoke"
        summary_path, command_result = run_smoke(args, out_dir)
    report = build_baseline_candidate_eval_loop_report(
        summary_path,
        command_result=command_result,
        min_overall_score_delta=args.min_overall_score_delta,
    )
    exit_code = resolve_exit_code(report, smoke_returncode=int(command_result.get("returncode") or 0), fail_on_reject=args.fail_on_reject)
    annotate_execution_summary(
        report,
        source_mode=source_mode,
        fail_on_reject=args.fail_on_reject,
        expected_exit_code=exit_code,
    )
    outputs = write_baseline_candidate_eval_loop_outputs(report, out_dir)
    print(render_baseline_candidate_eval_loop_text(report), end="")
    for key, path in outputs.items():
        print(f"saved_{key}={path}")
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


def run_smoke(args: argparse.Namespace, out_dir: Path) -> tuple[Path, dict[str, Any]]:
    smoke_dir = out_dir / "tiny-scorecard-comparison-smoke"
    check_dir = out_dir / "tiny-scorecard-comparison-smoke-check"
    logs_dir = out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    command = build_smoke_command(args, smoke_dir, check_dir)
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    stdout_path = logs_dir / "tiny_scorecard_comparison_smoke_stdout.txt"
    stderr_path = logs_dir / "tiny_scorecard_comparison_smoke_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    command_result = {
        "name": "tiny_scorecard_comparison_smoke",
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "command": command,
        "command_text": " ".join(command),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
    summary_path = smoke_dir / "tiny_scorecard_comparison_smoke_summary.json"
    if not summary_path.is_file():
        raise SystemExit(completed.returncode or 1)
    return summary_path, command_result


def resolve_exit_code(report: dict[str, Any], *, smoke_returncode: int, fail_on_reject: bool) -> int:
    if report.get("status") != "pass":
        return smoke_returncode or 1
    if fail_on_reject and report.get("decision") != "accept_candidate":
        return 2
    return 0


def annotate_execution_summary(
    report: dict[str, Any],
    *,
    source_mode: str,
    fail_on_reject: bool,
    expected_exit_code: int,
) -> dict[str, Any]:
    report["execution"] = {
        "source_mode": source_mode,
        "fail_on_reject": bool(fail_on_reject),
        "expected_exit_code": int(expected_exit_code),
        "gate_mode": "strict" if fail_on_reject else "exploratory",
    }
    return report


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def build_smoke_command(args: argparse.Namespace, smoke_dir: Path, check_dir: Path) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_tiny_scorecard_comparison_smoke.py"),
        "--out-dir",
        str(smoke_dir),
        "--suite-name",
        str(args.suite_name),
        "--case-token-cap",
        str(args.case_token_cap),
        "--max-iters",
        str(args.baseline_max_iters),
        "--baseline-max-iters",
        str(args.baseline_max_iters),
        "--candidate-max-iters",
        str(args.candidate_max_iters),
        "--decision-min-rubric-score",
        str(args.decision_min_rubric_score),
        "--eval-iters",
        str(args.eval_iters),
        "--batch-size",
        str(args.batch_size),
        "--block-size",
        str(args.block_size),
        "--n-layer",
        str(args.n_layer),
        "--n-head",
        str(args.n_head),
        "--n-embd",
        str(args.n_embd),
        "--baseline-seed",
        str(args.baseline_seed),
        "--candidate-seed",
        str(args.candidate_seed),
        "--summary-check-out-dir",
        str(check_dir),
        "--force",
    ]


if __name__ == "__main__":
    main()
