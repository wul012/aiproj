from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_repair_plan,
    locate_route_promotion_bounded_real_replay_review,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_repair_plan_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bounded real replay repair plan from replay review evidence.")
    parser.add_argument("--real-replay-review", type=Path, required=True, help="Bounded real replay review JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-repair-plan")
    parser.add_argument("--require-plan-ready", action="store_true", help="Return exit code 1 when the repair plan is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    review_path = locate_route_promotion_bounded_real_replay_review(args.real_replay_review)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_repair_plan(
        read_json_report(review_path),
        real_replay_review_path=review_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_repair_plan_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_plan_ready=args.require_plan_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
