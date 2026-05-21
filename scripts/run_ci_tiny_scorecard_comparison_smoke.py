from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]

PLAN_JSON_FILENAME = "ci_tiny_scorecard_smoke_plan.json"
PLAN_TEXT_FILENAME = "ci_tiny_scorecard_smoke_plan.txt"

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


def build_invocation_plan(args: argparse.Namespace, command: Sequence[str], *, returncode: int | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "wrapper": "run_ci_tiny_scorecard_comparison_smoke",
        "out_dir": str(args.out_dir),
        "summary_check_out_dir": str(args.summary_check_out_dir),
        "config": dict(CI_TINY_SCORECARD_CONFIG),
        "flags": {
            "summary_check_allow_gate_stop": bool(args.summary_check_allow_gate_stop),
            "summary_check_no_fail": bool(args.summary_check_no_fail),
            "force": bool(args.force),
        },
        "command": list(command),
        "command_text": " ".join(command),
        "returncode": returncode,
    }


def render_invocation_plan(plan: dict[str, Any]) -> str:
    config = plan["config"]
    flags = plan["flags"]
    rows = [
        ("schema_version", plan["schema_version"]),
        ("wrapper", plan["wrapper"]),
        ("out_dir", plan["out_dir"]),
        ("summary_check_out_dir", plan["summary_check_out_dir"]),
        ("suite_name", config["suite_name"]),
        ("case_token_cap", config["case_token_cap"]),
        ("baseline_max_iters", config["baseline_max_iters"]),
        ("candidate_max_iters", config["candidate_max_iters"]),
        ("decision_min_rubric_score", config["decision_min_rubric_score"]),
        ("eval_iters", config["eval_iters"]),
        ("batch_size", config["batch_size"]),
        ("block_size", config["block_size"]),
        ("n_embd", config["n_embd"]),
        ("baseline_seed", config["baseline_seed"]),
        ("candidate_seed", config["candidate_seed"]),
        ("summary_check_allow_gate_stop", flags["summary_check_allow_gate_stop"]),
        ("summary_check_no_fail", flags["summary_check_no_fail"]),
        ("force", flags["force"]),
        ("returncode", plan.get("returncode")),
        ("command_text", plan["command_text"]),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_invocation_plan(plan: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / PLAN_JSON_FILENAME,
        "text": out_dir / PLAN_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["text"].write_text(render_invocation_plan(plan), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    command = build_ci_smoke_command(args)
    completed = subprocess.run(command, check=False)
    plan = build_invocation_plan(args, command, returncode=completed.returncode)
    outputs = write_invocation_plan(plan, args.out_dir)
    print(f"ci_plan_json={outputs['json']}")
    print(f"ci_plan_text={outputs['text']}")
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
