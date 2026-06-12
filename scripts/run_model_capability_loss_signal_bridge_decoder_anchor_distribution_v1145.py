from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_loss_signal_bridge_decoder_anchor_distribution import (  # noqa: E402
    build_loss_signal_bridge_decoder_anchor_distribution,
    materialize_loss_signal_bridge_inputs,
    read_json_report,
    resolve_exit_code,
    run_loss_signal_bridge_training,
    write_loss_signal_bridge_decoder_anchor_distribution_outputs,
)
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402

DEFAULT_HOLDOUT_SCORECARD_REPORT = (
    ROOT
    / "f"
    / "1144"
    / "解释"
    / "model-capability-holdout-scorecard-smoke-v1144"
    / "model_capability_holdout_scorecard_smoke_v1144.json"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run v1145 bounded loss signal bridge training and decoder anchor distribution audit."
    )
    parser.add_argument("--holdout-scorecard-smoke", type=Path, default=DEFAULT_HOLDOUT_SCORECARD_REPORT)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "output" / "model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145",
    )
    parser.add_argument("--training-run-dir", type=Path, default=None, help="Reuse an existing training run instead of running scripts/train.py.")
    parser.add_argument("--device", choices=["cpu", "auto", "cuda"], default="cpu")
    parser.add_argument("--max-iters", type=int, default=40)
    parser.add_argument("--eval-interval", type=int, default=10)
    parser.add_argument("--eval-iters", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=1145)
    parser.add_argument("--require-pass", action="store_true", help="Return 1 if the report does not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    input_paths = materialize_loss_signal_bridge_inputs(args.out_dir / "loss-signal-bridge-inputs")
    if args.training_run_dir is None:
        training_run_dir = args.out_dir / "real-loss-signal-training-run"
        training_command = run_loss_signal_bridge_training(
            input_paths["corpus"],
            training_run_dir,
            train_script=ROOT / "scripts" / "train.py",
            device=args.device,
            max_iters=args.max_iters,
            eval_interval=args.eval_interval,
            eval_iters=args.eval_iters,
            seed=args.seed,
            learning_rate=args.learning_rate,
        )
    else:
        training_run_dir = args.training_run_dir
        training_command = {"mode": "reuse_existing_training_run", "run_dir": str(training_run_dir)}
    report = build_loss_signal_bridge_decoder_anchor_distribution(
        read_json_report(args.holdout_scorecard_smoke, description="v1144 holdout scorecard smoke"),
        read_json_report(input_paths["seed_revision"], description="decoder anchor seed revision"),
        read_json_report(input_paths["failure_diagnostic"], description="decoder anchor failure diagnostic"),
        corpus_path=input_paths["corpus"],
        training_run_dir=training_run_dir,
        distribution_out_dir=args.out_dir / "decoder-anchor-distribution-audit",
        holdout_scorecard_path=args.holdout_scorecard_smoke,
        seed_revision_path=input_paths["seed_revision"],
        diagnostic_path=input_paths["failure_diagnostic"],
        training_command=training_command,
    )
    outputs = write_loss_signal_bridge_decoder_anchor_distribution_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
