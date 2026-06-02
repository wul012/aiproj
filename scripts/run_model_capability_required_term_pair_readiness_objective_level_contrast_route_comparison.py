from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison import (  # noqa: E402
    build_objective_level_contrast_route_comparison,
    locate_objective_level_contrast_route_comparison_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison_artifacts import (  # noqa: E402
    render_objective_level_contrast_route_comparison_text,
    write_objective_level_contrast_route_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare fixed-preserving, near-exact, and objective-level contrast pair replay routes.")
    parser.add_argument("--baseline", type=Path, required=True, help="Baseline replay JSON or output directory.")
    parser.add_argument("--exact-repair", type=Path, required=True, help="Near-exact repair replay JSON or output directory.")
    parser.add_argument("--objective", type=Path, required=True, help="Objective-level contrast replay JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-objective-level-contrast-route-comparison")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when comparison checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    baseline = locate_objective_level_contrast_route_comparison_source(args.baseline)
    exact_repair = locate_objective_level_contrast_route_comparison_source(args.exact_repair)
    objective = locate_objective_level_contrast_route_comparison_source(args.objective)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_objective_level_contrast_route_comparison(
        read_json_report(baseline),
        read_json_report(exact_repair),
        read_json_report(objective),
        baseline_path=baseline,
        exact_repair_path=exact_repair,
        objective_path=objective,
    )
    outputs = write_objective_level_contrast_route_comparison_outputs(report, args.out_dir)
    print(render_objective_level_contrast_route_comparison_text(report), end="")
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
