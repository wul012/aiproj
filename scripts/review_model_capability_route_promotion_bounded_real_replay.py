from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_review import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_review,
    locate_route_promotion_bounded_real_replay,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_review_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_review_text,
    write_model_capability_route_promotion_bounded_real_replay_review_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review bounded real replay evidence and diagnose missed required terms.")
    parser.add_argument("--real-replay", type=Path, required=True, help="Bounded real replay JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-review")
    parser.add_argument("--minimum-pass-rate-for-repair-review", type=float, default=0.4)
    parser.add_argument("--require-review-pass", action="store_true", help="Return exit code 1 when review inputs fail.")
    parser.add_argument("--require-promotion-ready", action="store_true", help="Return exit code 1 unless all replay cases passed.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_route_promotion_bounded_real_replay(args.real_replay)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_review(
        read_json_report(replay_path),
        real_replay_path=replay_path,
        minimum_pass_rate_for_repair_review=args.minimum_pass_rate_for_repair_review,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_review_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_review_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_review_pass=args.require_review_pass,
        require_promotion_ready=args.require_promotion_ready,
    )
    if code:
        raise SystemExit(code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
