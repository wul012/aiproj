from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest import (  # noqa: E402
    build_objective_level_contrast_promotion_manifest,
    locate_objective_level_contrast_promotion_manifest_acceptance_review,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_manifest_artifacts import (  # noqa: E402
    render_objective_level_contrast_promotion_manifest_text,
    write_objective_level_contrast_promotion_manifest_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a promotion manifest from an objective-level contrast acceptance review.")
    parser.add_argument("--acceptance-review", type=Path, required=True, help="Acceptance review JSON or output directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-readiness-objective-level-contrast-promotion-manifest",
    )
    parser.add_argument("--route-id", default="objective_level_contrast")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when manifest checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    review_path = locate_objective_level_contrast_promotion_manifest_acceptance_review(args.acceptance_review)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_objective_level_contrast_promotion_manifest(
        read_json_report(review_path),
        source_acceptance_review_path=review_path,
        route_id=args.route_id,
    )
    outputs = write_objective_level_contrast_promotion_manifest_outputs(report, args.out_dir)
    print(render_objective_level_contrast_promotion_manifest_text(report), end="")
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
