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

from minigpt.model_capability_ladder_stability import parse_seed_list  # noqa: E402
from minigpt.model_capability_token_budget_probe import TOKEN_BUDGET_JSON_FILENAME, parse_token_caps  # noqa: E402
from minigpt.model_capability_token_budget_stability import (  # noqa: E402
    build_model_capability_token_budget_stability_report,
)
from minigpt.model_capability_token_budget_stability_artifacts import (  # noqa: E402
    render_model_capability_token_budget_stability_text,
    write_model_capability_token_budget_stability_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run token-budget probes across seeds and summarize stability.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-token-budget-stability")
    parser.add_argument("--seeds", default="1337,2026", help="Comma-separated seed replay list.")
    parser.add_argument("--token-caps", default="4,12", help="Comma-separated case token caps.")
    parser.add_argument("--max-iters-list", default="1,4", help="Comma-separated training step ladder for each token cap.")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
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
    token_caps = parse_token_caps(args.token_caps)
    prepare_output_dir(args.out_dir, force=args.force)
    logs_dir = args.out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    command_results = []
    for seed in seeds:
        seed_dir = args.out_dir / "seeds" / f"seed-{seed}"
        result = run_command(f"seed_{seed}_token_budget_probe", probe_command(args, seed_dir, seed, token_caps), logs_dir)
        command_results.append(result)
        report_path = seed_dir / TOKEN_BUDGET_JSON_FILENAME
        report = read_probe_report(report_path, seed=seed)
        report["report_path"] = str(report_path)
        reports.append(report)
    run_config = build_run_config(args, seeds, token_caps, command_results)
    stability_report = build_model_capability_token_budget_stability_report(
        reports,
        out_dir=args.out_dir,
        run_config=run_config,
    )
    stability_report["commands"] = command_results
    outputs = write_model_capability_token_budget_stability_outputs(stability_report, args.out_dir)
    print(render_model_capability_token_budget_stability_text(stability_report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    exit_code = resolve_exit_code(stability_report, require_pass=args.require_pass)
    if exit_code:
        raise SystemExit(exit_code)


def build_run_config(
    args: argparse.Namespace,
    seeds: list[int],
    token_caps: list[int],
    command_results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "suite_name": args.suite_name,
        "seeds": seeds,
        "token_caps": token_caps,
        "max_iters_list": args.max_iters_list,
        "eval_iters": args.eval_iters,
        "batch_size": args.batch_size,
        "block_size": args.block_size,
        "n_layer": args.n_layer,
        "n_head": args.n_head,
        "n_embd": args.n_embd,
        "command_count": len(command_results),
        "command_failure_count": sum(1 for item in command_results if item.get("status") != "pass"),
    }


def probe_command(args: argparse.Namespace, out_dir: Path, seed: int, token_caps: list[int]) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_model_capability_token_budget_probe.py"),
        "--out-dir",
        str(out_dir),
        "--token-caps",
        ",".join(str(item) for item in token_caps),
        "--max-iters-list",
        str(args.max_iters_list),
        "--suite-name",
        str(args.suite_name),
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


def read_probe_report(path: Path, *, seed: int) -> dict[str, Any]:
    if not path.is_file():
        return {
            "status": "fail",
            "decision": "missing_token_budget_probe",
            "token_budget_count": 0,
            "run_config": {"seed": seed},
            "summary": {},
        }
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        return payload
    return {
        "status": "fail",
        "decision": "invalid_token_budget_probe",
        "token_budget_count": 0,
        "run_config": {"seed": seed},
        "summary": {},
    }


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
