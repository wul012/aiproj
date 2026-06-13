"""v1160: train learned-absolute-position vs RoPE MiniGPT and compare held-out metrics.

Example:
    python scripts/run_rope_eval_v1160.py --device auto --steps 400
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
from minigpt.rope_eval_v1160 import RopeEvalConfig, run_rope_eval  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.templated_corpus import build_templated_corpus  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "rope_eval_v1160"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare learned positions vs RoPE on held-out generalization.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "rope-eval-v1160")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--max-sentences", type=int, default=400)
    parser.add_argument("--heldout-ratio", type=float, default=0.2)
    parser.add_argument("--block-size", type=int, default=48)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.seed)
    device = choose_device(args.device)

    corpus = build_templated_corpus(seed=args.seed, heldout_ratio=args.heldout_ratio, max_sentences=args.max_sentences)
    tokenizer = CharTokenizer.train(corpus.full_text)
    train_ids = torch.tensor(tokenizer.encode(corpus.train_text), dtype=torch.long)
    heldout_ids = torch.tensor(tokenizer.encode(corpus.heldout_text), dtype=torch.long)
    print(f"device={device} vocab={tokenizer.vocab_size} train_chars={len(corpus.train_text)} heldout_chars={len(corpus.heldout_text)}")

    config = RopeEvalConfig(
        steps=args.steps, lr=args.lr, batch_size=args.batch_size, block_size=args.block_size,
        n_layer=args.n_layer, n_head=args.n_head, n_embd=args.n_embd, seed=args.seed,
    )
    report = run_rope_eval(
        vocab_size=tokenizer.vocab_size, train_ids=train_ids, heldout_ids=heldout_ids,
        config=config, device=device, corpus_stats=corpus.stats(),
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
