from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_dual_objective_boundary_plan import (  # noqa: E402
    build_model_capability_required_term_pair_dual_objective_boundary_plan,
    locate_dual_objective_boundary_closeout,
    locate_dual_objective_boundary_miss_diagnostic,
    read_dual_objective_boundary_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_dual_objective_boundary_plan_artifacts import (  # noqa: E402
    render_dual_objective_boundary_plan_text,
    write_dual_objective_boundary_plan_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the required-term pair dual-objective boundary plan.")
    parser.add_argument("--closeout", type=Path, required=True, help="Resume/generation-internal closeout JSON or output dir.")
    parser.add_argument("--miss-diagnostic", type=Path, required=True, help="Constrained decode miss diagnostic JSON or output dir.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-dual-objective-boundary-plan")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    closeout_path = locate_dual_objective_boundary_closeout(args.closeout)
    miss_path = locate_dual_objective_boundary_miss_diagnostic(args.miss_diagnostic)
    report = build_model_capability_required_term_pair_dual_objective_boundary_plan(
        read_dual_objective_boundary_input(closeout_path),
        read_dual_objective_boundary_input(miss_path),
    )
    outputs = write_dual_objective_boundary_plan_outputs(report, args.out_dir)
    print(render_dual_objective_boundary_plan_text(report), end="")
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
