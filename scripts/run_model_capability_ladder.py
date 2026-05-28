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

from minigpt.model_capability_ladder import (  # noqa: E402
    build_model_capability_ladder_report,
    parse_max_iters_list,
    read_ladder_summary,
)
from minigpt.model_capability_ladder_artifacts import (  # noqa: E402
    render_model_capability_ladder_text,
    write_model_capability_ladder_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny MiniGPT training scale ladder and summarize capability signals.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-ladder")
    parser.add_argument("--max-iters-list", default="1,2,4", help="Comma-separated training step ladder.")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
    parser.add_argument("--case-token-cap", type=int, default=4)
    parser.add_argument("--eval-iters", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=8)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the ladder report fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.case_token_cap < 1:
        raise ValueError("--case-token-cap must be at least 1")
    max_iters_values = parse_max_iters_list(args.max_iters_list)
    prepare_output_dir(args.out_dir, force=args.force)
    logs_dir = args.out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    command_results = []
    for max_iters in max_iters_values:
        rung_dir = args.out_dir / "rungs" / f"max-iters-{max_iters}"
        result = run_command(f"max_iters_{max_iters}", tiny_smoke_command(args, rung_dir, max_iters), logs_dir)
        command_results.append(result)
        summary_path = rung_dir / "tiny_standard_benchmark_smoke_summary.json"
        summary = read_ladder_summary(summary_path)
        summary["summary_path"] = str(summary_path)
        summary["max_iters"] = max_iters
        summaries.append(summary)
        if result["returncode"] != 0:
            break
    run_config = build_run_config(args, max_iters_values, command_results)
    report = build_model_capability_ladder_report(summaries, out_dir=args.out_dir, run_config=run_config)
    report["commands"] = command_results
    outputs = write_model_capability_ladder_outputs(report, args.out_dir)
    print(render_model_capability_ladder_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    exit_code = resolve_exit_code(report, require_pass=args.require_pass)
    if exit_code:
        raise SystemExit(exit_code)


def build_run_config(args: argparse.Namespace, max_iters_values: list[int], command_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "suite_name": args.suite_name,
        "case_token_cap": args.case_token_cap,
        "max_iters_values": max_iters_values,
        "eval_iters": args.eval_iters,
        "batch_size": args.batch_size,
        "block_size": args.block_size,
        "n_layer": args.n_layer,
        "n_head": args.n_head,
        "n_embd": args.n_embd,
        "seed": args.seed,
        "command_count": len(command_results),
        "command_failure_count": sum(1 for item in command_results if item.get("status") != "pass"),
    }


def tiny_smoke_command(args: argparse.Namespace, out_dir: Path, max_iters: int) -> list[str]:
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
        str(args.seed),
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
