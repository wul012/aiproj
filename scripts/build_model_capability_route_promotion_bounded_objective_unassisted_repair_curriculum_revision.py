from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision import (  # noqa: E402
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision,
    locate_unassisted_repair_zero_hit_diagnostic,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision_artifacts import (  # noqa: E402
    render_bounded_objective_unassisted_repair_curriculum_revision_text,
    write_bounded_objective_unassisted_repair_curriculum_revision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bounded objective unassisted repair curriculum revision.")
    parser.add_argument("--zero-hit-diagnostic", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-objective-unassisted-repair-curriculum-revision")
    parser.add_argument("--require-revision-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    diagnostic_path = locate_unassisted_repair_zero_hit_diagnostic(args.zero_hit_diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision(
        read_json_report(diagnostic_path),
        zero_hit_diagnostic_path=diagnostic_path,
    )
    outputs = write_bounded_objective_unassisted_repair_curriculum_revision_outputs(report, args.out_dir)
    print(render_bounded_objective_unassisted_repair_curriculum_revision_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_revision_ready=args.require_revision_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
