from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_strategy_revision import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision,
    locate_repair_checkpoint_comparison,
    locate_repair_plan,
    locate_repair_seed,
    locate_repair_training_run,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a revised bounded replay repair strategy after a repair checkpoint comparison.")
    parser.add_argument("--comparison", type=Path, required=True, help="Repair checkpoint comparison JSON or output directory.")
    parser.add_argument("--repair-plan", type=Path, required=True, help="Original bounded real replay repair plan JSON or output directory.")
    parser.add_argument("--repair-seed", type=Path, required=True, help="Original bounded real replay repair seed JSON or output directory.")
    parser.add_argument("--training-run", type=Path, required=True, help="Repair training run evidence JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-repair-strategy-revision")
    parser.add_argument("--require-revision-ready", action="store_true", help="Return exit code 1 when strategy revision is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    comparison_path = locate_repair_checkpoint_comparison(args.comparison)
    plan_path = locate_repair_plan(args.repair_plan)
    seed_path = locate_repair_seed(args.repair_seed)
    training_path = locate_repair_training_run(args.training_run)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision(
        read_json_report(comparison_path),
        read_json_report(plan_path),
        read_json_report(seed_path),
        read_json_report(training_path),
        comparison_path=comparison_path,
        repair_plan_path=plan_path,
        repair_seed_path=seed_path,
        training_run_path=training_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_text(report), end="")
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
