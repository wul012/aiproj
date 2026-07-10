from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from minigpt.report_utils import as_dict  # noqa: E402
from minigpt.tiny_scorecard_comparison_smoke_outputs import (  # noqa: E402
    SUMMARY_JSON_FILENAME,  # noqa: F401
    SUMMARY_TEXT_FILENAME,  # noqa: F401
    format_counts,  # noqa: F401
    print_summary,
    render_summary,  # noqa: F401
    write_summary_and_optional_check,
    write_summary_outputs,  # noqa: F401
)
from minigpt.tiny_scorecard_comparison_smoke_summary import (  # noqa: E402
    artifact_status,  # noqa: F401
    build_summary,
    build_tiny_benchmark_history,  # noqa: F401
    comparison_summary,  # noqa: F401
    decision_summary,  # noqa: F401
    first_list_item,  # noqa: F401
    first_matching_list_item,  # noqa: F401
    first_name,  # noqa: F401
    first_threshold_block,  # noqa: F401
    float_or_none,  # noqa: F401
    history_summary,  # noqa: F401
    read_json,  # noqa: F401
    remediation_gate_status,  # noqa: F401
    smoke_summary,  # noqa: F401
    threshold_block_profile,  # noqa: F401
    threshold_blocks,  # noqa: F401
)
from scripts.check_tiny_scorecard_comparison_smoke import (  # noqa: E402
    check_summary as check_smoke_summary,  # noqa: F401
    write_check_outputs as write_smoke_check_outputs,  # noqa: F401
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run two CPU tiny standard benchmark smokes, compare their scorecards, and build a promotion decision."
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "tiny-scorecard-comparison-smoke")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
    parser.add_argument("--case-token-cap", type=int, default=12)
    parser.add_argument("--max-iters", type=int, default=1)
    parser.add_argument(
        "--baseline-max-iters",
        type=int,
        default=None,
        help="Override --max-iters for the baseline tiny training run.",
    )
    parser.add_argument(
        "--candidate-max-iters",
        type=int,
        default=None,
        help="Override --max-iters for the candidate tiny training run.",
    )
    parser.add_argument(
        "--decision-min-rubric-score",
        type=float,
        default=80.0,
        help="Minimum rubric average score passed to the scorecard promotion decision.",
    )
    parser.add_argument(
        "--require-clean-remediation",
        action="store_true",
        help="Fail the smoke when the decision report contains remediation rows.",
    )
    parser.add_argument(
        "--summary-check-out-dir",
        type=Path,
        default=None,
        help="Optionally validate the generated smoke summary and write check JSON/text sidecars.",
    )
    parser.add_argument(
        "--summary-check-allow-gate-stop",
        action="store_true",
        help="Let the inline summary checker accept an expected strict remediation gate stop.",
    )
    parser.add_argument(
        "--summary-check-no-fail",
        action="store_true",
        help="Write inline summary-check outputs without failing the smoke on summary-check failures.",
    )
    parser.add_argument("--eval-iters", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=8)
    parser.add_argument("--baseline-seed", type=int, default=1337)
    parser.add_argument("--candidate-seed", type=int, default=2026)
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.case_token_cap < 1:
        raise ValueError("--case-token-cap must be at least 1")
    if args.max_iters < 1:
        raise ValueError("--max-iters must be at least 1")
    run_config = build_run_config(args)
    if int(run_config["baseline_max_iters"]) < 1:
        raise ValueError("--baseline-max-iters must be at least 1")
    if int(run_config["candidate_max_iters"]) < 1:
        raise ValueError("--candidate-max-iters must be at least 1")
    out_dir = args.out_dir
    if out_dir.exists() and any(out_dir.iterdir()):
        if not args.force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    baseline_dir = out_dir / "baseline"
    candidate_dir = out_dir / "candidate"
    comparison_dir = out_dir / "scorecard-comparison"
    decision_dir = out_dir / "scorecard-decision"
    history_dir = out_dir / "benchmark-history"
    commands = [
        ("baseline_smoke", tiny_smoke_command(args, baseline_dir, args.baseline_seed, int(run_config["baseline_max_iters"]))),
        ("candidate_smoke", tiny_smoke_command(args, candidate_dir, args.candidate_seed, int(run_config["candidate_max_iters"]))),
        (
            "scorecard_comparison",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "compare_benchmark_scorecards.py"),
                str(baseline_dir / "run"),
                str(candidate_dir / "run"),
                "--name",
                "tiny-baseline",
                "--name",
                "tiny-candidate",
                "--baseline",
                "tiny-baseline",
                "--out-dir",
                str(comparison_dir),
                "--title",
                "MiniGPT tiny scorecard comparison smoke",
            ],
        ),
        (
            "scorecard_decision",
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "build_benchmark_scorecard_decision.py"),
                str(comparison_dir),
                "--out-dir",
                str(decision_dir),
                "--min-rubric-score",
                str(run_config["decision_min_rubric_score"]),
                "--title",
                "MiniGPT tiny scorecard decision smoke",
            ],
        ),
    ]

    command_results = []
    for name, command in commands:
        result = run_command(name, command, logs_dir)
        command_results.append(result)
        if result["returncode"] != 0:
            summary = build_summary(
                out_dir=out_dir,
                baseline_dir=baseline_dir,
                candidate_dir=candidate_dir,
                comparison_dir=comparison_dir,
                decision_dir=decision_dir,
                history_dir=history_dir,
                run_config=run_config,
                command_results=command_results,
                issues=[f"{name} command returned {result['returncode']}"],
            )
            outputs = write_summary_and_optional_check(
                summary,
                out_dir,
                summary_check_out_dir=args.summary_check_out_dir,
                summary_check_allow_gate_stop=args.summary_check_allow_gate_stop,
            )
            print_summary(summary, outputs)
            raise SystemExit(int(result["returncode"] or 1))

    summary = build_summary(
        out_dir=out_dir,
        baseline_dir=baseline_dir,
        candidate_dir=candidate_dir,
        comparison_dir=comparison_dir,
        decision_dir=decision_dir,
        history_dir=history_dir,
        run_config=run_config,
        command_results=command_results,
        issues=[],
    )
    outputs = write_summary_and_optional_check(
        summary,
        out_dir,
        summary_check_out_dir=args.summary_check_out_dir,
        summary_check_allow_gate_stop=args.summary_check_allow_gate_stop,
    )
    print_summary(summary, outputs)
    summary_check = as_dict(summary.get("summary_check"))
    if summary_check.get("status") == "fail" and not args.summary_check_no_fail:
        raise SystemExit(1)
    if summary["status"] != "pass":
        raise SystemExit(1)


def build_run_config(args: argparse.Namespace) -> dict[str, Any]:
    baseline_max_iters = int(args.baseline_max_iters if args.baseline_max_iters is not None else args.max_iters)
    candidate_max_iters = int(args.candidate_max_iters if args.candidate_max_iters is not None else args.max_iters)
    decision_min_rubric_score = float(args.decision_min_rubric_score)
    if not 0.0 <= decision_min_rubric_score <= 100.0:
        raise ValueError("--decision-min-rubric-score must be between 0 and 100")
    max_iters_delta = candidate_max_iters - baseline_max_iters
    if max_iters_delta > 0:
        budget_mode = "candidate_more_iters"
    elif max_iters_delta < 0:
        budget_mode = "candidate_fewer_iters"
    else:
        budget_mode = "matched_iters"
    return {
        "suite_name": args.suite_name,
        "case_token_cap": args.case_token_cap,
        "baseline_max_iters": baseline_max_iters,
        "candidate_max_iters": candidate_max_iters,
        "max_iters_delta": max_iters_delta,
        "budget_mode": budget_mode,
        "decision_min_rubric_score": decision_min_rubric_score,
        "require_clean_remediation": bool(args.require_clean_remediation),
        "summary_check_requested": getattr(args, "summary_check_out_dir", None) is not None,
        "summary_check_allow_gate_stop": bool(getattr(args, "summary_check_allow_gate_stop", False)),
        "summary_check_no_fail": bool(getattr(args, "summary_check_no_fail", False)),
        "eval_iters": args.eval_iters,
        "batch_size": args.batch_size,
        "block_size": args.block_size,
        "n_layer": args.n_layer,
        "n_head": args.n_head,
        "n_embd": args.n_embd,
        "baseline_seed": args.baseline_seed,
        "candidate_seed": args.candidate_seed,
    }


def tiny_smoke_command(args: argparse.Namespace, out_dir: Path, seed: int, max_iters: int) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_tiny_standard_benchmark_smoke.py"),
        "--out-dir",
        str(out_dir),
        "--suite-name",
        str(args.suite_name),
        "--case-token-cap",
        str(args.case_token_cap),
        "--max-iters",
        str(max_iters),
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
        "--seed",
        str(seed),
        "--force",
    ]


def run_command(name: str, command: list[str], logs_dir: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    stdout_path = logs_dir / f"{name}_stdout.txt"
    stderr_path = logs_dir / f"{name}_stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    return {
        "name": name,
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "command": command,
        "command_text": " ".join(command),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }


if __name__ == "__main__":
    main()
