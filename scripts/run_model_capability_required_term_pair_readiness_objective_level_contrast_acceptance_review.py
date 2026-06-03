from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review import (  # noqa: E402
    build_objective_level_contrast_acceptance_review,
    locate_objective_level_contrast_acceptance_review_rollup,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_acceptance_review_artifacts import (  # noqa: E402
    render_objective_level_contrast_acceptance_review_text,
    write_objective_level_contrast_acceptance_review_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review an objective-level contrast seed-stability rollup for acceptance.")
    parser.add_argument("--rollup", type=Path, required=True, help="Seed-stability rollup JSON or output directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-readiness-objective-level-contrast-acceptance-review",
    )
    parser.add_argument("--minimum-pair-full-count", type=int, default=2)
    parser.add_argument("--require-uniform-strength", action="store_true")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when acceptance review fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    rollup_path = locate_objective_level_contrast_acceptance_review_rollup(args.rollup)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_objective_level_contrast_acceptance_review(
        read_json_report(rollup_path),
        source_rollup_path=rollup_path,
        minimum_pair_full_count=args.minimum_pair_full_count,
        require_uniform_strength=args.require_uniform_strength,
    )
    outputs = write_objective_level_contrast_acceptance_review_outputs(report, args.out_dir)
    print(render_objective_level_contrast_acceptance_review_text(report), end="")
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
