from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_objective_closeout import (  # noqa: E402
    build_model_capability_required_term_pair_objective_closeout,
    locate_branch_binding_decision,
    locate_target_anchor_decision,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_objective_closeout_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_objective_closeout_text,
    write_model_capability_required_term_pair_objective_closeout_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close out current required-term pair objectives before a loss-branch route.")
    parser.add_argument("--branch-binding", type=Path, required=True, help="Branch-binding decision JSON or output directory.")
    parser.add_argument("--target-anchor", type=Path, required=True, help="Target-anchor decision JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-objective-closeout")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when closeout is not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    branch_path = locate_branch_binding_decision(args.branch_binding)
    target_path = locate_target_anchor_decision(args.target_anchor)
    report = build_model_capability_required_term_pair_objective_closeout(
        branch_binding_decision=read_json_report(branch_path),
        target_anchor_decision=read_json_report(target_path),
        branch_binding_path=branch_path,
        target_anchor_path=target_path,
    )
    outputs = write_model_capability_required_term_pair_objective_closeout_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_objective_closeout_text(report), end="")
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
