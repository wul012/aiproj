from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_ladder import parse_max_iters_list, read_ladder_summary  # noqa: E402
from minigpt.model_capability_ladder_stability import (  # noqa: E402
    build_model_capability_ladder_stability_report,
    parse_seed_list,
)
from minigpt.model_capability_ladder_stability_artifacts import (  # noqa: E402
    render_model_capability_ladder_stability_text,
    write_model_capability_ladder_stability_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run multiple MiniGPT capability ladders and summarize seed stability.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-ladder-stability")
    parser.add_argument("--seeds", default="1337,2026", help="Comma-separated seed replay list.")
    parser.add_argument("--max-iters-list", default="1,2,4", help="Comma-separated training step ladder.")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
    parser.add_argument("--case-token-cap", type=int, default=4)
    parser.add_argument("--eval-iters", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=8)
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the stability report fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seeds = parse_seed_list(args.seeds)
    max_iters_values = parse_max_iters_list(args.max_iters_list)
    prepare_output_dir(args.out_dir, force=args.force)
    logs_dir = args.out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    command_results = []
    for seed in seeds:
        ladder_dir = args.out_dir / "seeds" / f"seed-{seed}"
        result = run_command(f"seed_{seed}", ladder_command(args, ladder_dir, seed, max_iters_values), logs_dir)
        command_results.append(result)
        report_path = ladder_dir / "model_capability_ladder.json"
        report = read_ladder_summary(report_path)
        report["report_path"] = str(report_path)
        if not report:
            report = {
                "status": "fail",
                "decision": "missing_ladder_report",
                "report_path": str(report_path),
                "run_config": {"seed": seed, "max_iters_values": max_iters_values},
                "trend_summary": {},
            }
        reports.append(report)
    run_config = build_run_config(args, seeds, max_iters_values, command_results)
    stability_report = build_model_capability_ladder_stability_report(reports, out_dir=args.out_dir, run_config=run_config)
    stability_report["commands"] = command_results
    outputs = write_model_capability_ladder_stability_outputs(stability_report, args.out_dir)
    print(render_model_capability_ladder_stability_text(stability_report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    exit_code = resolve_exit_code(stability_report, require_pass=args.require_pass)
    if exit_code:
        raise SystemExit(exit_code)


def build_run_config(
    args: argparse.Namespace,
    seeds: list[int],
    max_iters_values: list[int],
    command_results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "suite_name": args.suite_name,
        "case_token_cap": args.case_token_cap,
        "seeds": seeds,
        "max_iters_values": max_iters_values,
        "eval_iters": args.eval_iters,
        "batch_size": args.batch_size,
        "block_size": args.block_size,
        "n_layer": args.n_layer,
        "n_head": args.n_head,
        "n_embd": args.n_embd,
        "command_count": len(command_results),
        "command_failure_count": sum(1 for item in command_results if item.get("status") != "pass"),
    }


def ladder_command(args: argparse.Namespace, out_dir: Path, seed: int, max_iters_values: list[int]) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_model_capability_ladder.py"),
        "--out-dir",
        str(out_dir),
        "--max-iters-list",
        ",".join(str(item) for item in max_iters_values),
        "--suite-name",
        str(args.suite_name),
        "--case-token-cap",
        str(args.case_token_cap),
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
        "--require-pass",
        "--force",
    ]


def run_command(name: str, command: list[str], logs_dir: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True, env=single_thread_env())
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


def single_thread_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")
    return env


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    main()
