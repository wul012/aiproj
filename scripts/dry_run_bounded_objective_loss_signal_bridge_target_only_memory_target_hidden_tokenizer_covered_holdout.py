from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run import (  # noqa: E402
    build_target_hidden_tokenizer_covered_holdout_dry_run,
    locate_target_hidden_tokenizer_covered_holdout_suite,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run_artifacts import (  # noqa: E402
    render_target_hidden_tokenizer_covered_holdout_dry_run_text,
    write_target_hidden_tokenizer_covered_holdout_dry_run_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run the target-hidden tokenizer-covered holdout suite scoring contract.")
    parser.add_argument("--holdout-suite", type=Path, required=True, help="v902 holdout suite JSON or output directory.")
    parser.add_argument("--positive-continuation", default=" fixed loss")
    parser.add_argument("--negative-continuation", default=" fixed only")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-target-hidden-tokenizer-covered-holdout-dry-run",
    )
    parser.add_argument("--require-dry-run-ready", action="store_true", help="Return exit code 1 when dry-run checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    suite_path = locate_target_hidden_tokenizer_covered_holdout_suite(args.holdout_suite)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_target_hidden_tokenizer_covered_holdout_dry_run(
        read_json_report(suite_path),
        positive_continuation=args.positive_continuation,
        negative_continuation=args.negative_continuation,
        holdout_suite_path=suite_path,
    )
    outputs = write_target_hidden_tokenizer_covered_holdout_dry_run_outputs(report, args.out_dir)
    print(render_target_hidden_tokenizer_covered_holdout_dry_run_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_dry_run_ready=args.require_dry_run_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
