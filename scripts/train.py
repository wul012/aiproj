from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dataset import get_batch, load_text, split_token_ids
from minigpt.model import GPTConfig, MiniGPT
from minigpt.tokenizer import CharTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a tiny GPT language model.")
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "sample_zh.txt")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--max-iters", type=int, default=1000)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--eval-iters", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--train-ratio", type=float, default=0.9)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


@torch.no_grad()
def estimate_loss(
    model: MiniGPT,
    train_data: torch.Tensor,
    val_data: torch.Tensor,
    block_size: int,
    batch_size: int,
    eval_iters: int,
    device: torch.device,
) -> dict[str, float]:
    model.eval()
    out: dict[str, float] = {}
    for split, data in [("train", train_data), ("val", val_data)]:
        losses = torch.empty(eval_iters)
        for k in range(eval_iters):
            x, y = get_batch(data, block_size, batch_size, device)
            _, loss = model(x, y)
            if loss is None:
                raise RuntimeError("Expected a loss during evaluation")
            losses[k] = loss.item()
        out[split] = float(losses.mean())
    model.train()
    return out


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)

    device = choose_device(args.device)
    text = load_text(args.data)
    tokenizer = CharTokenizer.train(text)
    token_ids = tokenizer.encode(text)
    train_data, val_data = split_token_ids(token_ids, train_ratio=args.train_ratio)

    config = GPTConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=args.block_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd,
        dropout=args.dropout,
    )
    model = MiniGPT(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    print(f"device={device}")
    print(f"tokens={len(token_ids)} vocab_size={tokenizer.vocab_size}")
    print(f"parameters={model.parameter_count():,}")

    last_loss = None
    for step in range(1, args.max_iters + 1):
        x, y = get_batch(train_data, args.block_size, args.batch_size, device)
        _, loss = model(x, y)
        if loss is None:
            raise RuntimeError("Expected a loss during training")

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        last_loss = float(loss.item())

        if step == 1 or step % args.eval_interval == 0 or step == args.max_iters:
            losses = estimate_loss(
                model=model,
                train_data=train_data,
                val_data=val_data,
                block_size=args.block_size,
                batch_size=args.batch_size,
                eval_iters=args.eval_iters,
                device=device,
            )
            print(f"step={step:5d} train_loss={losses['train']:.4f} val_loss={losses['val']:.4f}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model": model.state_dict(),
        "config": asdict(config),
        "last_loss": last_loss,
        "step": args.max_iters,
    }
    torch.save(checkpoint, args.out_dir / "checkpoint.pt")
    tokenizer.save(args.out_dir / "tokenizer.json")
    (args.out_dir / "train_config.json").write_text(
        json.dumps(vars(args) | {"device_used": str(device)}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"saved={args.out_dir}")


if __name__ == "__main__":
    main()
