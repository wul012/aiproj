from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_candidate_promotion_packet import (  # noqa: E402
    build_randomized_holdout_candidate_promotion_packet,
    locate_randomized_holdout_dry_run,
    locate_randomized_holdout_real_replay,
    locate_randomized_holdout_replay_review,
    locate_randomized_holdout_suite,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_candidate_promotion_packet_artifacts import (  # noqa: E402
    render_randomized_holdout_candidate_promotion_packet_text,
    write_randomized_holdout_candidate_promotion_packet_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a randomized holdout candidate promotion packet from suite, dry-run, replay, and review evidence.")
    parser.add_argument("--replay-review", type=Path, required=True)
    parser.add_argument("--real-replay", type=Path, required=True)
    parser.add_argument("--dry-run", type=Path, required=True)
    parser.add_argument("--holdout-suite", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "randomized-holdout-candidate-promotion-packet")
    parser.add_argument("--require-packet-ready", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    review_path = locate_randomized_holdout_replay_review(args.replay_review)
    real_path = locate_randomized_holdout_real_replay(args.real_replay)
    dry_path = locate_randomized_holdout_dry_run(args.dry_run)
    suite_path = locate_randomized_holdout_suite(args.holdout_suite)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_candidate_promotion_packet(
        read_json_report(review_path),
        read_json_report(real_path),
        read_json_report(dry_path),
        read_json_report(suite_path),
        replay_review_path=review_path,
        real_replay_path=real_path,
        dry_run_path=dry_path,
        holdout_suite_path=suite_path,
    )
    outputs = write_randomized_holdout_candidate_promotion_packet_outputs(report, args.out_dir)
    print(render_randomized_holdout_candidate_promotion_packet_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(report, require_packet_ready=args.require_packet_ready, require_promotion_ready=args.require_promotion_ready)
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
