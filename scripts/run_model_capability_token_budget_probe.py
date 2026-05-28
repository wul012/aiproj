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

from minigpt.model_capability_ladder import read_ladder_summary  # noqa: E402
from minigpt.model_capability_stall_diagnostic import build_model_capability_stall_diagnostic  # noqa: E402
from minigpt.model_capability_stall_diagnostic_artifacts import (  # noqa: E402
    write_model_capability_stall_diagnostic_outputs,
)
from minigpt.model_capability_token_budget_probe import (  # noqa: E402
    build_model_capability_token_budget_probe_report,
    parse_token_caps,
)
from minigpt.model_capability_token_budget_probe_artifacts import (  # noqa: E402
    render_model_capability_token_budget_probe_text,
    write_model_capability_token_budget_probe_outputs,
)
from minigpt.report_utils import as_dict, write_json_payload  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run tiny capability ladders across token caps and compare stall diagnostics.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-token-budget-probe")
    parser.add_argument("--token-caps", default="4,12", help="Comma-separated case token caps.")
    parser.add_argument("--max-iters-list", default="1,4", help="Comma-separated training step ladder for each token cap.")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default="standard-zh")
    parser.add_argument("--eval-iters", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=8)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the probe fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    token_caps = parse_token_caps(args.token_caps)
    prepare_output_dir(args.out_dir, force=args.force)
    command_results: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for token_cap in token_caps:
        cap_dir = args.out_dir / f"token-cap-{token_cap}"
        ladder_dir = cap_dir / "ladder"
        logs_dir = cap_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        result = run_command(f"token_cap_{token_cap}_ladder", ladder_command(args, token_cap, ladder_dir), logs_dir)
        command_results.append(result)
        ladder_report_path = ladder_dir / "model_capability_ladder.json"
        ladder = read_ladder_summary(ladder_report_path)
        stability = build_single_ladder_stability(ladder, ladder_report_path)
        stability_path = cap_dir / "model_capability_ladder_single_seed_stability.json"
        write_json_payload(stability, stability_path)
        diagnostic_dir = cap_dir / "stall-diagnostic"
        diagnostic = build_model_capability_stall_diagnostic(
            stability,
            out_dir=diagnostic_dir,
            source_path=stability_path,
            search_base=ROOT,
        )
        diagnostic["case_token_cap"] = token_cap
        diagnostic["source_ladder_report"] = str(ladder_report_path)
        diagnostic["source_diagnostic"] = str(diagnostic_dir)
        diagnostic["run_config"] = {"case_token_cap": token_cap, "seed": args.seed, "max_iters_list": args.max_iters_list}
        write_model_capability_stall_diagnostic_outputs(diagnostic, diagnostic_dir)
        diagnostics.append(diagnostic)
        if result["returncode"] != 0:
            break
    run_config = build_run_config(args, token_caps, command_results)
    report = build_model_capability_token_budget_probe_report(diagnostics, out_dir=args.out_dir, run_config=run_config)
    report["commands"] = command_results
    outputs = write_model_capability_token_budget_probe_outputs(report, args.out_dir)
    print(render_model_capability_token_budget_probe_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if args.require_pass and report.get("status") != "pass":
        raise SystemExit(1)


def ladder_command(args: argparse.Namespace, token_cap: int, out_dir: Path) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(ROOT / "scripts" / "run_model_capability_ladder.py"),
        "--out-dir",
        str(out_dir),
        "--max-iters-list",
        str(args.max_iters_list),
        "--suite-name",
        str(args.suite_name),
        "--case-token-cap",
        str(token_cap),
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
        "--require-pass",
        "--force",
    ]


def build_single_ladder_stability(ladder: dict[str, Any], ladder_report_path: Path) -> dict[str, Any]:
    trend = as_dict(ladder.get("trend_summary"))
    config = as_dict(ladder.get("run_config"))
    return {
        "schema_version": 1,
        "status": "pass" if ladder.get("status") == "pass" else "fail",
        "decision": "single_seed_ladder_ready" if ladder.get("status") == "pass" else "fix_single_seed_ladder",
        "rows": [
            {
                "seed": config.get("seed"),
                "status": ladder.get("status"),
                "decision": ladder.get("decision"),
                "report_path": str(ladder_report_path),
                "rung_count": ladder.get("rung_count"),
                "successful_rung_count": ladder.get("successful_rung_count"),
                "max_iters_values": ladder.get("max_iters_values"),
                "trend_decision": trend.get("decision"),
                "first_max_iters": trend.get("first_max_iters"),
                "last_max_iters": trend.get("last_max_iters"),
                "best_loss_max_iters": trend.get("best_loss_max_iters"),
                "best_score_max_iters": trend.get("best_score_max_iters"),
                "best_val_loss_delta": trend.get("best_val_loss_delta_first_to_last"),
                "score_delta": trend.get("score_delta_first_to_last"),
                "generation_flags_delta": trend.get("generation_flags_delta_first_to_last"),
            }
        ],
    }


def build_run_config(args: argparse.Namespace, token_caps: list[int], command_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "suite_name": args.suite_name,
        "token_caps": token_caps,
        "max_iters_list": args.max_iters_list,
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


if __name__ == "__main__":
    main()
