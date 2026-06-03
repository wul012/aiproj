from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_consumer_plan import (  # noqa: E402
    build_model_capability_route_promotion_consumer_plan,
    locate_route_promotion_downstream_guard,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_consumer_plan_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_consumer_plan_text,
    write_model_capability_route_promotion_consumer_plan_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bounded route-promotion consumer plan.")
    parser.add_argument("--downstream-guard", type=Path, required=True, help="Downstream guard JSON or output directory.")
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-consumer-plan")
    parser.add_argument("--require-ready-plan", action="store_true", help="Return exit code 1 when the consumer plan is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    guard_path = locate_route_promotion_downstream_guard(args.downstream_guard)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_consumer_plan(
        read_json_report(guard_path),
        downstream_guard_path=guard_path,
        required_boundary=args.required_boundary,
    )
    outputs = write_model_capability_route_promotion_consumer_plan_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_consumer_plan_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_ready_plan=args.require_ready_plan):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
