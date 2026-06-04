from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic import (  # noqa: E402
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic,
    locate_curriculum_patch_replay_comparison,
    locate_seed_revision_replay_comparison,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_artifacts import (  # noqa: E402
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_text,
    write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose case-level shape migration between seed revision and curriculum patch bounded-objective replays.")
    parser.add_argument("--seed-revision-replay", type=Path, required=True)
    parser.add_argument("--curriculum-patch-replay", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "bounded-objective-curriculum-patch-shape-migration-diagnostic")
    parser.add_argument("--require-diagnostic-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_path = locate_seed_revision_replay_comparison(args.seed_revision_replay)
    patch_path = locate_curriculum_patch_replay_comparison(args.curriculum_patch_replay)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic(
        read_json_report(seed_path),
        read_json_report(patch_path),
        seed_revision_replay_path=seed_path,
        curriculum_patch_replay_path=patch_path,
    )
    outputs = write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_outputs(report, args.out_dir)
    print(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_diagnostic_ready=args.require_diagnostic_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
