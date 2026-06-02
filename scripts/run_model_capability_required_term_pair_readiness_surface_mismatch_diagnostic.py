from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_surface_mismatch_diagnostic import (  # noqa: E402
    build_surface_mismatch_diagnostic,
    locate_surface_mismatch_contract_source,
    locate_surface_mismatch_training_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_surface_mismatch_diagnostic_artifacts import (  # noqa: E402
    render_surface_mismatch_diagnostic_text,
    write_surface_mismatch_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose direct prompt surface mismatch after objective-structure pair-readiness training.")
    parser.add_argument("--contract", type=Path, required=True, help="Objective-structure contract JSON or output directory.")
    parser.add_argument("--training-run", type=Path, required=True, help="Pair-readiness training run JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-surface-mismatch-diagnostic")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when diagnostic checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    contract_source = locate_surface_mismatch_contract_source(args.contract)
    training_source = locate_surface_mismatch_training_source(args.training_run)
    report = build_surface_mismatch_diagnostic(
        contract_report=read_json_report(contract_source),
        training_report=read_json_report(training_source),
        contract_path=contract_source,
        training_path=training_source,
    )
    outputs = write_surface_mismatch_diagnostic_outputs(report, args.out_dir)
    print(render_surface_mismatch_diagnostic_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
