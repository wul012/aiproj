from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay import (  # noqa: E402
    build_tokenizer_coverage_aware_holdout_real_replay,
    locate_tokenizer_coverage_aware_holdout_dry_run,
    locate_tokenizer_coverage_aware_holdout_suite,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay_artifacts import (  # noqa: E402
    render_tokenizer_coverage_aware_holdout_real_replay_text,
    write_tokenizer_coverage_aware_holdout_real_replay_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real replay for the tokenizer-coverage-aware holdout suite.")
    parser.add_argument("--holdout-suite", type=Path, required=True)
    parser.add_argument("--dry-run", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-tokenizer-coverage-aware-holdout-real-replay")
    parser.add_argument("--require-execution-pass", action="store_true")
    parser.add_argument("--require-model-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    suite_path = locate_tokenizer_coverage_aware_holdout_suite(args.holdout_suite)
    dry_run_path = locate_tokenizer_coverage_aware_holdout_dry_run(args.dry_run)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_tokenizer_coverage_aware_holdout_real_replay(
        read_json_report(suite_path),
        read_json_report(dry_run_path),
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        holdout_suite_path=suite_path,
        dry_run_path=dry_run_path,
    )
    outputs = write_tokenizer_coverage_aware_holdout_real_replay_outputs(report, args.out_dir)
    print(render_tokenizer_coverage_aware_holdout_real_replay_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(report, require_execution_pass=args.require_execution_pass, require_model_pass=args.require_model_pass)
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
