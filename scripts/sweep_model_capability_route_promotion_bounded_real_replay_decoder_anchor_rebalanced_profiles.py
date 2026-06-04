from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep,
    locate_benchmark_suite,
    locate_dry_run,
    locate_failure_diagnostic,
    locate_suite_review,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sweep decoder profiles for a rebalanced decoder-anchor MiniGPT checkpoint.")
    parser.add_argument("--benchmark-suite", type=Path, required=True)
    parser.add_argument("--suite-review", type=Path, required=True)
    parser.add_argument("--dry-run", type=Path, required=True)
    parser.add_argument("--failure-diagnostic", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-profile-sweep")
    parser.add_argument("--require-sweep-ready", action="store_true")
    parser.add_argument("--require-recovery", action="store_true")
    parser.add_argument("--require-promotion", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    suite_path = locate_benchmark_suite(args.benchmark_suite)
    review_path = locate_suite_review(args.suite_review)
    dry_run_path = locate_dry_run(args.dry_run)
    diagnostic_path = locate_failure_diagnostic(args.failure_diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep(
        read_json_report(review_path),
        read_json_report(suite_path),
        read_json_report(dry_run_path),
        read_json_report(diagnostic_path),
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        suite_review_path=review_path,
        benchmark_suite_path=suite_path,
        dry_run_path=dry_run_path,
        failure_diagnostic_path=diagnostic_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_sweep_ready=args.require_sweep_ready,
        require_recovery=args.require_recovery,
        require_promotion=args.require_promotion,
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
