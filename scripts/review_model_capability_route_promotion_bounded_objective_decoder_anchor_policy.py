from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review import (  # noqa: E402
    build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review,
    locate_decoder_anchor_policy_replay,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review_artifacts import (  # noqa: E402
    render_bounded_objective_decoder_anchor_policy_review_text,
    write_bounded_objective_decoder_anchor_policy_review_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review bounded objective decoder anchor policy replay evidence.")
    parser.add_argument("--policy-replay", type=Path, required=True, help="Bounded objective decoder anchor policy replay JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-objective-decoder-anchor-policy-review")
    parser.add_argument("--require-review-ready", action="store_true", help="Return exit code 1 when review inputs are not ready.")
    parser.add_argument("--require-branch-closed", action="store_true", help="Return exit code 1 unless the assisted anchor path is closed.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_decoder_anchor_policy_replay(args.policy_replay)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review(
        read_json_report(replay_path),
        policy_replay_path=replay_path,
    )
    outputs = write_bounded_objective_decoder_anchor_policy_review_outputs(report, args.out_dir)
    print(render_bounded_objective_decoder_anchor_policy_review_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_review_ready=args.require_review_ready,
        require_branch_closed=args.require_branch_closed,
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
