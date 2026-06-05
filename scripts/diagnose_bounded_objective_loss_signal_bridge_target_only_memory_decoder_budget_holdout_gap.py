from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic import (  # noqa: E402
    build_decoder_budget_holdout_gap_diagnostic,
    locate_decoder_budget_holdout_replay,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic_artifacts import (  # noqa: E402
    render_decoder_budget_holdout_gap_diagnostic_text,
    write_decoder_budget_holdout_gap_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose tokenizer/corpus/prompt gaps behind decoder-budget holdout replay failures.")
    parser.add_argument("--holdout-replay", type=Path, required=True, help="v896 holdout replay JSON or output directory.")
    parser.add_argument("--tokenizer", type=Path, required=True, help="Tokenizer JSON used by the replay checkpoint.")
    parser.add_argument("--training-corpus", type=Path, required=True, help="Prepared training corpus used by the replay checkpoint.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-holdout-gap-diagnostic",
    )
    parser.add_argument("--require-diagnostic-ready", action="store_true", help="Return exit code 1 when diagnostic inputs fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    holdout_path = locate_decoder_budget_holdout_replay(args.holdout_replay)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_decoder_budget_holdout_gap_diagnostic(
        read_json_report(holdout_path),
        tokenizer_path=args.tokenizer,
        training_corpus_path=args.training_corpus,
        holdout_replay_path=holdout_path,
    )
    outputs = write_decoder_budget_holdout_gap_diagnostic_outputs(report, args.out_dir)
    print(render_decoder_budget_holdout_gap_diagnostic_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_diagnostic_ready=args.require_diagnostic_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
