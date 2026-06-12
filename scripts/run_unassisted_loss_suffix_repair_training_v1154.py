from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402
from minigpt.unassisted_loss_suffix_repair_training_run_v1154 import (  # noqa: E402
    build_unassisted_loss_suffix_repair_training_run_v1154,
    default_v1153_seed_corpus_path,
    locate_v1153_seed_corpus,
    read_json_report,
    resolve_exit_code,
    seed_corpus_text_path,
    write_unassisted_loss_suffix_repair_training_run_v1154_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and verify the v1154 bounded unassisted loss-suffix repair training.")
    parser.add_argument("--seed-corpus", type=Path, default=default_v1153_seed_corpus_path(ROOT), help="v1153 seed corpus JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "unassisted-loss-suffix-repair-training-run-v1154")
    parser.add_argument("--run-dir", type=Path, default=None, help="Training run directory; defaults to <out-dir>/run.")
    parser.add_argument("--run-training", action="store_true", help="Execute scripts/train.py before building evidence.")
    parser.add_argument("--require-training-ready", action="store_true", help="Return 1 if training evidence is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--block-size", type=int, default=24)
    parser.add_argument("--max-iters", type=int, default=60)
    parser.add_argument("--eval-interval", type=int, default=10)
    parser.add_argument("--eval-iters", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--train-ratio", type=float, default=0.85)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1154)
    parser.add_argument("--sample-prompt", type=str, default="answer:")
    parser.add_argument("--sample-tokens", type=int, default=12)
    parser.add_argument("--sample-temperature", type=float, default=0.2)
    parser.add_argument("--sample-top-k", type=int, default=5)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_path = locate_v1153_seed_corpus(args.seed_corpus)
    run_dir = args.run_dir or args.out_dir / "run"
    prepare_output_dir(args.out_dir, force=args.force)
    seed_report = read_json_report(seed_path, description="v1153 unassisted loss suffix repair seed corpus")
    if args.run_training:
        run_training(args, seed_corpus_text_path(seed_path), run_dir)
    report = build_unassisted_loss_suffix_repair_training_run_v1154(seed_report, run_dir, seed_corpus_path=seed_path)
    outputs = write_unassisted_loss_suffix_repair_training_run_v1154_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_training_ready=args.require_training_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def run_training(args: argparse.Namespace, prepared_data: Path, run_dir: Path) -> None:
    if not prepared_data.is_file():
        raise SystemExit(f"v1153 seed corpus text is missing: {prepared_data}")
    command = [
        sys.executable,
        str(ROOT / "scripts" / "train.py"),
        "--prepared-data",
        str(prepared_data),
        "--out-dir",
        str(run_dir),
        "--tokenizer",
        "char",
        "--batch-size",
        str(args.batch_size),
        "--block-size",
        str(args.block_size),
        "--max-iters",
        str(args.max_iters),
        "--eval-interval",
        str(args.eval_interval),
        "--eval-iters",
        str(args.eval_iters),
        "--learning-rate",
        str(args.learning_rate),
        "--train-ratio",
        str(args.train_ratio),
        "--n-layer",
        str(args.n_layer),
        "--n-head",
        str(args.n_head),
        "--n-embd",
        str(args.n_embd),
        "--dropout",
        str(args.dropout),
        "--seed",
        str(args.seed),
        "--device",
        "cpu",
        "--sample-prompt",
        args.sample_prompt,
        "--sample-tokens",
        str(args.sample_tokens),
        "--sample-temperature",
        str(args.sample_temperature),
        "--sample-top-k",
        str(args.sample_top_k),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
