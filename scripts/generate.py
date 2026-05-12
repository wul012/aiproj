from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model import GPTConfig, MiniGPT
from minigpt.tokenizer import load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate text with a trained MiniGPT checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--prompt", type=str, default="人工智能")
    parser.add_argument("--max-new-tokens", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out", type=Path, default=None, help="Optional file path for generated text")
    return parser.parse_args()


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    prompt_ids = tokenizer.encode(args.prompt)
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    out = model.generate(
        idx,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
    )
    generated = tokenizer.decode(out[0].tolist())
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(generated, encoding="utf-8")
        print(f"saved={args.out}")
    else:
        print(generated)


if __name__ == "__main__":
    main()
