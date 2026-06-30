from __future__ import annotations

import argparse
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

try:
    from scripts._engineering_health import (
        EngineeringHealthStep,
        EngineeringHealthStepResult,
        build_steps,
        build_summary,
        write_summary_outputs,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _engineering_health import (
        EngineeringHealthStep,
        EngineeringHealthStepResult,
        build_steps,
        build_summary,
        write_summary_outputs,
    )

Runner = Callable[..., subprocess.CompletedProcess[str]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MiniGPT engineering health checks.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "engineering-health")
    return parser.parse_args(argv)


def run_steps(
    steps: Sequence[EngineeringHealthStep],
    *,
    runner: Runner = subprocess.run,
    summary_out_dir: Path | None = None,
) -> int:
    first_failure = 0
    results: list[EngineeringHealthStepResult] = []
    for step in steps:
        command = list(step.command)
        print(f"Running {step.step_id}:", flush=True)
        print(subprocess.list2cmdline(command), flush=True)
        completed = runner(command, cwd=ROOT, check=False, stderr=subprocess.STDOUT)
        return_code = int(completed.returncode)
        results.append(EngineeringHealthStepResult(step.step_id, tuple(command), return_code))
        status = "pass" if return_code == 0 else "fail"
        print(f"{step.step_id}={status}", flush=True)
        if return_code and not first_failure:
            first_failure = return_code
    if summary_out_dir is not None:
        summary = build_summary(tuple(results), summary_out_dir)
        outputs = write_summary_outputs(summary, summary_out_dir)
        print(f"summary_json={outputs['json']}", flush=True)
        print(f"summary_markdown={outputs['markdown']}", flush=True)
    return first_failure


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    return run_steps(build_steps(out_dir), summary_out_dir=out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
