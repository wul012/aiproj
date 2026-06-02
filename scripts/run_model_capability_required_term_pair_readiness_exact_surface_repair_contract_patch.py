from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch import (  # noqa: E402
    build_exact_surface_repair_contract_patch,
    locate_exact_surface_repair_contract_patch_base,
    locate_exact_surface_repair_contract_patch_plan,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch_artifacts import (  # noqa: E402
    render_exact_surface_repair_contract_patch_text,
    write_exact_surface_repair_contract_patch_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply a checked exact-surface repair contract patch.")
    parser.add_argument("--repair-plan", required=True, type=Path, help="Exact-surface repair plan JSON or output directory.")
    parser.add_argument("--base-contract", required=True, type=Path, help="Fixed-preserving transfer contract JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-exact-surface-repair-contract-patch")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when patching fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    plan_source = locate_exact_surface_repair_contract_patch_plan(args.repair_plan)
    base_source = locate_exact_surface_repair_contract_patch_base(args.base_contract)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_exact_surface_repair_contract_patch(
        repair_plan=read_json_report(plan_source),
        base_contract_report=read_json_report(base_source),
        repair_plan_path=plan_source,
        base_contract_path=base_source,
    )
    outputs = write_exact_surface_repair_contract_patch_outputs(report, args.out_dir)
    print(render_exact_surface_repair_contract_patch_text(report), end="")
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
