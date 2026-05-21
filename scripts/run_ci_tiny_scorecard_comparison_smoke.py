from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]

CI_TINY_SCORECARD_CONFIG = {
    "suite_name": "standard-zh",
    "case_token_cap": 3,
    "max_iters": 1,
    "baseline_max_iters": 1,
    "candidate_max_iters": 2,
    "decision_min_rubric_score": 60.0,
    "eval_iters": 1,
    "batch_size": 2,
    "block_size": 8,
    "n_embd": 8,
    "baseline_seed": 1337,
    "candidate_seed": 2026,
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the CI-sized tiny scorecard comparison smoke with inline summary-check sidecars."
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "tiny-scorecard-comparison-smoke-ci")
    parser.add_argument(
        "--summary-check-out-dir",
        type=Path,
        default=ROOT / "runs" / "tiny-scorecard-comparison-smoke-check-ci",
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
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def build_ci_smoke_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_tiny_scorecard_comparison_smoke.py"),
        "--out-dir",
        str(args.out_dir),
        "--suite-name",
        str(CI_TINY_SCORECARD_CONFIG["suite_name"]),
        "--case-token-cap",
        str(CI_TINY_SCORECARD_CONFIG["case_token_cap"]),
        "--max-iters",
        str(CI_TINY_SCORECARD_CONFIG["max_iters"]),
        "--baseline-max-iters",
        str(CI_TINY_SCORECARD_CONFIG["baseline_max_iters"]),
        "--candidate-max-iters",
        str(CI_TINY_SCORECARD_CONFIG["candidate_max_iters"]),
        "--decision-min-rubric-score",
        str(CI_TINY_SCORECARD_CONFIG["decision_min_rubric_score"]),
        "--eval-iters",
        str(CI_TINY_SCORECARD_CONFIG["eval_iters"]),
        "--batch-size",
        str(CI_TINY_SCORECARD_CONFIG["batch_size"]),
        "--block-size",
        str(CI_TINY_SCORECARD_CONFIG["block_size"]),
        "--n-embd",
        str(CI_TINY_SCORECARD_CONFIG["n_embd"]),
        "--baseline-seed",
        str(CI_TINY_SCORECARD_CONFIG["baseline_seed"]),
        "--candidate-seed",
        str(CI_TINY_SCORECARD_CONFIG["candidate_seed"]),
        "--summary-check-out-dir",
        str(args.summary_check_out_dir),
    ]
    if args.summary_check_allow_gate_stop:
        command.append("--summary-check-allow-gate-stop")
    if args.summary_check_no_fail:
        command.append("--summary-check-no-fail")
    if args.force:
        command.append("--force")
    return command


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    completed = subprocess.run(build_ci_smoke_command(args), check=False)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
