from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard import (  # noqa: E402
    build_objective_level_contrast_promotion_guard,
    locate_promotion_guard_comparison,
    locate_promotion_guard_replay,
    locate_promotion_guard_training,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard_artifacts import (  # noqa: E402
    render_objective_level_contrast_promotion_guard_text,
    write_objective_level_contrast_promotion_guard_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a guarded promotion check for the objective-level contrast route.")
    parser.add_argument("--comparison", type=Path, required=True, help="Objective-level contrast route comparison JSON or output directory.")
    parser.add_argument("--replay", type=Path, required=True, help="Objective-level contrast replay JSON or output directory.")
    parser.add_argument("--training", type=Path, required=True, help="Objective-level contrast training JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-objective-level-contrast-promotion-guard")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when guard checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    comparison = locate_promotion_guard_comparison(args.comparison)
    replay = locate_promotion_guard_replay(args.replay)
    training = locate_promotion_guard_training(args.training)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_objective_level_contrast_promotion_guard(
        read_json_report(comparison),
        read_json_report(replay),
        read_json_report(training),
        comparison_path=comparison,
        replay_path=replay,
        training_path=training,
    )
    outputs = write_objective_level_contrast_promotion_guard_outputs(report, args.out_dir)
    print(render_objective_level_contrast_promotion_guard_text(report), end="")
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
