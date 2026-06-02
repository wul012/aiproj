from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_structured_template_contract import (  # noqa: E402
    build_structured_template_contract,
    locate_structured_template_contract_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_structured_template_contract_artifacts import (  # noqa: E402
    render_structured_template_contract_text,
    write_structured_template_contract_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a structured-template pair-readiness contract after the loss-retention route regresses.")
    parser.add_argument("comparison", type=Path, help="Pair-readiness repair comparison JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-structured-template-contract")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when contract checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source = locate_structured_template_contract_source(args.comparison)
    report = build_structured_template_contract(read_json_report(source), source_path=source)
    outputs = write_structured_template_contract_outputs(report, args.out_dir)
    print(render_structured_template_contract_text(report), end="")
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
