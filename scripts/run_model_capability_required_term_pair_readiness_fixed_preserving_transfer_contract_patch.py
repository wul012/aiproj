from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch import (  # noqa: E402
    build_fixed_preserving_transfer_contract_patch,
    locate_fixed_preserving_transfer_contract_patch_base,
    locate_fixed_preserving_transfer_contract_patch_plan,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch_artifacts import (  # noqa: E402
    render_fixed_preserving_transfer_contract_patch_text,
    write_fixed_preserving_transfer_contract_patch_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch a direct-completion contract with fixed-preserving transfer rows.")
    parser.add_argument("--transfer-plan", type=Path, required=True, help="Fixed-preserving transfer plan JSON or output directory.")
    parser.add_argument("--base-contract", type=Path, required=True, help="Direct-completion surface contract JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "fixed-preserving-transfer-contract-patch")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when patch checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    plan_source = locate_fixed_preserving_transfer_contract_patch_plan(args.transfer_plan)
    base_source = locate_fixed_preserving_transfer_contract_patch_base(args.base_contract)
    report = build_fixed_preserving_transfer_contract_patch(
        transfer_plan=read_json_report(plan_source),
        base_contract_report=read_json_report(base_source),
        transfer_plan_path=plan_source,
        base_contract_path=base_source,
    )
    outputs = write_fixed_preserving_transfer_contract_patch_outputs(report, args.out_dir)
    print(render_fixed_preserving_transfer_contract_patch_text(report), end="")
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
