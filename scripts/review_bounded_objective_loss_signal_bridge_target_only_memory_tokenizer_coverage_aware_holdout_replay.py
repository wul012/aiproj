from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review import (  # noqa: E402
    build_tokenizer_coverage_aware_holdout_replay_review,
    locate_holdout_real_replay,
    locate_holdout_suite,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_artifacts import (  # noqa: E402
    render_tokenizer_coverage_aware_holdout_replay_review_text,
    write_tokenizer_coverage_aware_holdout_replay_review_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review tokenizer-covered holdout replay for target leakage and promotion readiness.")
    parser.add_argument("--real-replay", type=Path, required=True)
    parser.add_argument("--holdout-suite", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-replay-review")
    parser.add_argument("--require-review-ready", action="store_true")
    parser.add_argument("--require-approval", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_holdout_real_replay(args.real_replay)
    suite_path = locate_holdout_suite(args.holdout_suite)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_tokenizer_coverage_aware_holdout_replay_review(
        read_json_report(replay_path),
        read_json_report(suite_path),
        real_replay_path=replay_path,
        holdout_suite_path=suite_path,
    )
    outputs = write_tokenizer_coverage_aware_holdout_replay_review_outputs(report, args.out_dir)
    print(render_tokenizer_coverage_aware_holdout_replay_review_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(report, require_review_ready=args.require_review_ready, require_approval=args.require_approval)
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
