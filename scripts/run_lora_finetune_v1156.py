"""v1156: train a small MiniGPT base, then LoRA-fine-tune only the adapters.

Produces the standard 5-format readability artifact set comparing validation and
training loss before vs after LoRA adaptation, plus a compact adapter file. This
is real model work: the loss numbers come from actual training on the GPU (or
CPU fallback), not from fixtures.

Example:
    python scripts/run_lora_finetune_v1156.py --device auto --base-steps 400 --lora-steps 400
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dataset import load_text, split_token_ids  # noqa: E402
from minigpt.lm_training import train_lm  # noqa: E402
from minigpt.lora import lora_state_dict, merge_lora  # noqa: E402
from minigpt.lora_finetune import LoRAFinetuneConfig, run_lora_finetune  # noqa: E402
from minigpt.model import GPTConfig, MiniGPT  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "lora_finetune_v1156"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a tiny MiniGPT base then LoRA fine-tune the adapters.")
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "sample_zh.txt")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "lora-finetune-v1156")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "runs" / "lora_v1156")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--block-size", type=int, default=32)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--base-steps", type=int, default=200)
    parser.add_argument("--base-lr", type=float, default=3e-4)
    parser.add_argument("--base-batch-size", type=int, default=32)
    parser.add_argument("--lora-steps", type=int, default=400)
    parser.add_argument("--lora-lr", type=float, default=1e-3)
    parser.add_argument("--lora-batch-size", type=int, default=32)
    parser.add_argument("--r", type=int, default=8)
    parser.add_argument("--alpha", type=float, default=16.0)
    parser.add_argument("--lora-dropout", type=float, default=0.0)
    parser.add_argument("--eval-iters", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1337)
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
    text = load_text(args.data)
    tokenizer = CharTokenizer.train(text)
    token_ids = tokenizer.encode(text)
    train_data, val_data = split_token_ids(token_ids, train_ratio=0.9)

    config = GPTConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=args.block_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd,
        dropout=0.0,
    )
    model = MiniGPT(config).to(device)
    print(f"device={device} tokens={len(token_ids)} vocab={tokenizer.vocab_size} params={model.parameter_count():,}")

    print("== training frozen base ==")
    train_lm(
        model,
        list(model.parameters()),
        train_data,
        steps=args.base_steps,
        lr=args.base_lr,
        batch_size=args.base_batch_size,
        block_size=config.block_size,
        device=device,
        log_every=max(1, args.base_steps // 5),
        label="base",
    )

    print("== LoRA fine-tuning adapters only ==")
    ft_config = LoRAFinetuneConfig(
        r=args.r,
        alpha=args.alpha,
        dropout=args.lora_dropout,
        steps=args.lora_steps,
        batch_size=args.lora_batch_size,
        learning_rate=args.lora_lr,
        eval_iters=args.eval_iters,
        seed=args.seed,
    )
    report = run_lora_finetune(model, train_data, val_data, config=ft_config, device=device)

    # Persist artifacts and a compact adapter.
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    adapter = lora_state_dict(model)
    torch.save({"lora_state_dict": adapter, "lora_config": asdict(ft_config), "model_config": asdict(config)}, args.runs_dir / "adapter.pt")
    tokenizer.save(args.runs_dir / "tokenizer.json")
    merged = merge_lora(model)  # prove serving path works; checkpoint is base+adapter merged
    torch.save({"model": model.state_dict(), "config": asdict(config), "merged_lora": True}, args.runs_dir / "checkpoint_merged.pt")

    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    print(f"adapter={args.runs_dir / 'adapter.pt'} merged_adapters={merged}")
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
