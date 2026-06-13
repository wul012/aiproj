"""v1158: LoRA domain adaptation between two sentence structures sharing one vocabulary.

Trains a base on the source structure, confirms a structural domain gap on the
target structure's held-out split, then adapts a frozen copy with LoRA (and a
full-fine-tune reference) to the target. Demonstrates the LoRA win v1157 predicted.

Example:
    python scripts/run_lora_domain_adaptation_v1158.py --device auto --base-steps 400 --adapt-steps 400
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.lora_domain_adaptation_v1158 import DomainAdaptationConfig, run_lora_domain_adaptation  # noqa: E402
from minigpt.model import GPTConfig, MiniGPT  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.templated_corpus import build_templated_corpus  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "lora_domain_adaptation_v1158"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoRA domain adaptation across sentence structures.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "lora-domain-adaptation-v1158")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--max-sentences", type=int, default=400)
    parser.add_argument("--heldout-ratio", type=float, default=0.2)
    parser.add_argument("--block-size", type=int, default=48)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--base-steps", type=int, default=400)
    parser.add_argument("--adapt-steps", type=int, default=400)
    parser.add_argument("--adapt-lr", type=float, default=1e-3)
    parser.add_argument("--r", type=int, default=8)
    parser.add_argument("--alpha", type=float, default=16.0)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args(argv)


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but torch.cuda.is_available() is False")
    return torch.device(name)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)
    device = choose_device(args.device)

    source = build_templated_corpus(seed=args.seed, heldout_ratio=args.heldout_ratio, max_sentences=args.max_sentences, structure="declarative")
    target = build_templated_corpus(seed=args.seed, heldout_ratio=args.heldout_ratio, max_sentences=args.max_sentences, structure="reordered")
    # Shared tokenizer over both domains; vocabularies are identical by construction.
    tokenizer = CharTokenizer.train(source.full_text + target.full_text)
    enc = lambda text: torch.tensor(tokenizer.encode(text), dtype=torch.long)  # noqa: E731
    print(f"source vocab={len(set(source.full_text))} target vocab={len(set(target.full_text))} shared vocab={tokenizer.vocab_size}")

    config = GPTConfig(vocab_size=tokenizer.vocab_size, block_size=args.block_size, n_layer=args.n_layer, n_head=args.n_head, n_embd=args.n_embd, dropout=0.0)
    model = MiniGPT(config).to(device)
    print(f"device={device} params={model.parameter_count():,}")

    eval_config = DomainAdaptationConfig(
        base_steps=args.base_steps, adapt_steps=args.adapt_steps, adapt_lr=args.adapt_lr,
        block_size=args.block_size, batch_size=args.batch_size, r=args.r, alpha=args.alpha, seed=args.seed,
    )
    report = run_lora_domain_adaptation(
        model, enc(source.train_text), enc(source.heldout_text), enc(target.train_text), enc(target.heldout_text),
        config=eval_config, device=device, corpus_stats={"source": source.stats(), "target": target.stats()},
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
