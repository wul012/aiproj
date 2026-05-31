from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_fixed_retention_objective_readiness import (  # noqa: E402
    build_model_capability_required_term_pair_fixed_retention_objective_readiness,
    locate_fixed_retention_diagnostic,
    locate_fixed_retention_route_decision,
    read_fixed_retention_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_readiness_artifacts import (  # noqa: E402
    render_fixed_retention_objective_readiness_text,
    write_fixed_retention_objective_readiness_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a fixed-retention objective readiness gate.")
    parser.add_argument("--route-decision", type=Path, required=True, help="Loss-branch route decision JSON or directory.")
    parser.add_argument("--diagnostic", type=Path, required=True, help="Missed-seed diagnostic JSON or directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-fixed-retention-objective-readiness")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when readiness inputs fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    route_source = locate_fixed_retention_route_decision(args.route_decision)
    diagnostic_source = locate_fixed_retention_diagnostic(args.diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_fixed_retention_objective_readiness(
        route_decision=read_fixed_retention_input(route_source),
        diagnostic=read_fixed_retention_input(diagnostic_source),
        route_decision_path=route_source,
        diagnostic_path=diagnostic_source,
    )
    outputs = write_fixed_retention_objective_readiness_outputs(report, args.out_dir)
    print(render_fixed_retention_objective_readiness_text(report), end="")
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
