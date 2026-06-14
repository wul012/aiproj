"""v1164: supervised fine-tuning for instruction-following on string ops.

Trains a tiny MiniGPT from scratch on an instruction dataset (copy/reverse/sort)
with completion-only loss masking, and measures held-out exact-match per op via
greedy generation. Runs a completion-only vs full-sequence-loss ablation.

Example:
    python scripts/run_sft_instruction_v1164.py --device auto --seeds 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus  # noqa: E402
from minigpt.sft_instruction_v1164 import SftInstructionConfig, run_sft_instruction  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "sft_instruction_v1164"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SFT instruction-following with completion-only loss.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "sft-instruction-v1164")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--corpus-seed", type=int, default=1337)
    parser.add_argument("--ops", type=str, nargs="+", default=["C", "R", "S"])
    parser.add_argument("--lengths", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--inputs-per-op-length", type=int, default=240)
    parser.add_argument("--heldout-ratio", type=float, default=0.25)
    parser.add_argument("--seeds", type=int, default=3, help="number of model-init seeds (1337..)")
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--step-schedule", type=int, nargs="+", default=[150, 400, 800, 1500])
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--full-loss-only", action="store_true", help="run only the full_loss arm")
    parser.add_argument("--completion-only", action="store_true", help="run only the completion_only arm")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.corpus_seed)
    device = choose_device(args.device)

    corpus = build_sft_corpus(
        seed=args.corpus_seed, ops=tuple(args.ops), lengths=tuple(args.lengths),
        inputs_per_op_length=args.inputs_per_op_length, heldout_ratio=args.heldout_ratio,
    )
    tokenizer = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
    pad_id = tokenizer.encode(PAD)[0]
    eos_id = tokenizer.encode(EOS)[0]

    train_examples = [(tokenizer.encode(e.text), len(e.prompt)) for e in corpus.train]
    heldout = [(tokenizer.encode(e.prompt), tokenizer.encode(e.expected_output), e.op) for e in corpus.heldout]
    stats = corpus.stats()
    block_size = max(16, corpus.max_text_len)
    max_new_tokens = max(args.lengths) + 2
    print(
        f"device={device} vocab={tokenizer.vocab_size} train={len(train_examples)} "
        f"heldout={len(heldout)} block_size={block_size}"
    )

    arms = ("completion_only", "full_loss")
    if args.full_loss_only:
        arms = ("full_loss",)
    elif args.completion_only:
        arms = ("completion_only",)

    config = SftInstructionConfig(
        block_size=block_size, seeds=tuple(1337 + i for i in range(args.seeds)), arms=arms,
        step_schedule=tuple(args.step_schedule), lr=args.lr, batch_size=args.batch_size,
        n_layer=args.n_layer, n_head=args.n_head, n_embd=args.n_embd, max_new_tokens=max_new_tokens,
    )
    report = run_sft_instruction(
        vocab_size=tokenizer.vocab_size, train_examples=train_examples, heldout=heldout,
        ops=tuple(args.ops), pad_id=pad_id, eos_id=eos_id, config=config, device=device, corpus_stats=stats,
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
