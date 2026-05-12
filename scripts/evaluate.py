from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dataset import get_batch, load_text, split_token_ids
from minigpt.model import GPTConfig, MiniGPT
from minigpt.prediction import perplexity_from_loss
from minigpt.tokenizer import load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a MiniGPT checkpoint on local text data.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "sample_zh.txt")
    parser.add_argument("--split", choices=["train", "val"], default="val")
    parser.add_argument("--train-ratio", type=float, default=0.9)
    parser.add_argument("--eval-iters", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--out", type=Path, default=None)
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
    data: torch.Tensor,
    block_size: int,
    batch_size: int,
    eval_iters: int,
    device: torch.device,
) -> float:
    model.eval()
    losses = torch.empty(eval_iters)
    for i in range(eval_iters):
        x, y = get_batch(data, block_size, batch_size, device)
        _, loss = model(x, y)
        if loss is None:
            raise RuntimeError("Expected evaluation loss")
        losses[i] = loss.item()
    return float(losses.mean())


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    device = choose_device(args.device)
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])

    text = load_text(args.data)
    token_ids = tokenizer.encode(text)
    train_data, val_data = split_token_ids(token_ids, train_ratio=args.train_ratio)
    data = train_data if args.split == "train" else val_data
    loss = estimate_loss(model, data, config.block_size, args.batch_size, args.eval_iters, device)

    report = {
        "checkpoint": str(args.checkpoint),
        "data": str(args.data),
        "split": args.split,
        "tokenizer": getattr(tokenizer, "name", "unknown"),
        "tokens": len(token_ids),
        "vocab_size": tokenizer.vocab_size,
        "block_size": config.block_size,
        "eval_iters": args.eval_iters,
        "batch_size": args.batch_size,
        "loss": round(loss, 8),
        "perplexity": round(perplexity_from_loss(loss), 8),
    }
    out_path = args.out or args.checkpoint.parent / "eval_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"saved={out_path}")


if __name__ == "__main__":
    main()
