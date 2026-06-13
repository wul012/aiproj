"""v1157: build a templated corpus, then measure LoRA's held-out generalization gain.

Trains a frozen base on the train split, evaluates it on a disjoint held-out
split, LoRA-adapts the frozen base, and re-evaluates — reporting whether the
adapter improves held-out loss/accuracy while training only ~3% of parameters.

Example:
    python scripts/run_lora_heldout_eval_v1157.py --device auto --base-steps 300 --lora-steps 300
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.lora_finetune import LoRAFinetuneConfig  # noqa: E402
from minigpt.lora_heldout_eval_v1157 import HeldoutEvalConfig, run_lora_heldout_eval  # noqa: E402
from minigpt.model import GPTConfig, MiniGPT  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.templated_corpus import build_templated_corpus  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "lora_heldout_eval_v1157"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure LoRA held-out generalization on a templated corpus.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "lora-heldout-eval-v1157")
    parser.add_argument("--corpus-out", type=Path, default=ROOT / "data" / "templated_corpus_v1157.txt")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--max-sentences", type=int, default=400)
    parser.add_argument("--heldout-ratio", type=float, default=0.2)
    parser.add_argument("--block-size", type=int, default=48)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--base-steps", type=int, default=300)
    parser.add_argument("--base-lr", type=float, default=3e-4)
    parser.add_argument("--lora-steps", type=int, default=300)
    parser.add_argument("--lora-lr", type=float, default=1e-3)
    parser.add_argument("--r", type=int, default=8)
    parser.add_argument("--alpha", type=float, default=16.0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--attention-only", action="store_true", help="Adapt only c_attn/c_proj instead of all linears.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.seed)
    device = choose_device(args.device)

    corpus = build_templated_corpus(seed=args.seed, heldout_ratio=args.heldout_ratio, max_sentences=args.max_sentences)
    args.corpus_out.parent.mkdir(parents=True, exist_ok=True)
    args.corpus_out.write_text(corpus.full_text, encoding="utf-8")
    stats = corpus.stats()
    print(f"corpus train_chars={stats['train_char_count']} heldout_chars={stats['heldout_char_count']} vocab={stats['vocab_char_count']}")

    tokenizer = CharTokenizer.train(corpus.full_text)  # vocab coverage over both splits
    train_ids = torch.tensor(tokenizer.encode(corpus.train_text), dtype=torch.long)
    heldout_ids = torch.tensor(tokenizer.encode(corpus.heldout_text), dtype=torch.long)

    config = GPTConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=args.block_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd,
        dropout=0.0,
    )
    model = MiniGPT(config).to(device)
    print(f"device={device} vocab={tokenizer.vocab_size} params={model.parameter_count():,}")

    eval_config = HeldoutEvalConfig(
        base_steps=args.base_steps,
        base_lr=args.base_lr,
        base_batch_size=args.batch_size,
        block_size=args.block_size,
        lora=LoRAFinetuneConfig(
            r=args.r, alpha=args.alpha, steps=args.lora_steps, batch_size=args.batch_size,
            learning_rate=args.lora_lr, seed=args.seed, target_all_linear=not args.attention_only,
        ),
    )
    report = run_lora_heldout_eval(
        model, train_ids, heldout_ids, config=eval_config, device=device, corpus_stats=stats
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
