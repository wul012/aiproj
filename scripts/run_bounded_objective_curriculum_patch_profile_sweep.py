from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_curriculum_patch_profile_sweep import (  # noqa: E402
    build_bounded_objective_curriculum_patch_profile_sweep,
    locate_curriculum_patch_training_run,
    locate_objective_contract,
    locate_shape_migration_diagnostic,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_curriculum_patch_profile_sweep_artifacts import (  # noqa: E402
    render_curriculum_patch_profile_sweep_text,
    write_curriculum_patch_profile_sweep_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a bounded-objective decode profile sweep for the curriculum patch checkpoint.")
    parser.add_argument("--objective-contract", type=Path, required=True)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--shape-diagnostic", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "bounded-objective-curriculum-patch-profile-sweep")
    parser.add_argument("--require-sweep-ready", action="store_true")
    parser.add_argument("--require-any-profile-recovered", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    contract_path = locate_objective_contract(args.objective_contract)
    training_path = locate_curriculum_patch_training_run(args.training_run)
    diagnostic_path = locate_shape_migration_diagnostic(args.shape_diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_bounded_objective_curriculum_patch_profile_sweep(
        read_json_report(contract_path),
        read_json_report(training_path),
        read_json_report(diagnostic_path),
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        objective_contract_path=contract_path,
        training_run_path=training_path,
        shape_migration_diagnostic_path=diagnostic_path,
    )
    outputs = write_curriculum_patch_profile_sweep_outputs(report, args.out_dir)
    print(render_curriculum_patch_profile_sweep_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_sweep_ready=args.require_sweep_ready,
        require_any_profile_recovered=args.require_any_profile_recovered,
    )
    if code:
        raise SystemExit(code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
