from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_repair_seed,
    locate_route_promotion_bounded_real_replay,
    locate_route_promotion_bounded_real_replay_repair_plan,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_repair_seed_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build bounded real replay repair seed examples from a repair plan and source replay.")
    parser.add_argument("--repair-plan", type=Path, required=True, help="Bounded real replay repair plan JSON or output directory.")
    parser.add_argument("--real-replay", type=Path, required=True, help="Bounded real replay JSON or output directory with source prompts.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-repair-seed")
    parser.add_argument("--require-seed-ready", action="store_true", help="Return exit code 1 when the repair seed is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    plan_path = locate_route_promotion_bounded_real_replay_repair_plan(args.repair_plan)
    replay_path = locate_route_promotion_bounded_real_replay(args.real_replay)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_repair_seed(
        read_json_report(plan_path),
        read_json_report(replay_path),
        repair_plan_path=plan_path,
        real_replay_path=replay_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_repair_seed_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_seed_ready=args.require_seed_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
