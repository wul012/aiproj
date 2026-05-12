from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model import GPTConfig, MiniGPT
from minigpt.prediction import top_k_predictions, write_predictions_svg
from minigpt.tokenizer import load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect next-token predictions for a MiniGPT checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--prompt", type=str, default="人工智能")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
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
    out_dir = args.out_dir or args.checkpoint.parent / "predictions"
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    prompt_ids = tokenizer.encode(args.prompt)
    if len(prompt_ids) > config.block_size:
        prompt_ids = prompt_ids[-config.block_size :]
    if not prompt_ids:
        raise ValueError("Prompt produced no token ids")

    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    with torch.no_grad():
        logits, _ = model(idx)
    predictions = top_k_predictions(
        logits[0, -1, :].detach().cpu(),
        tokens=tokenizer.itos,
        k=args.top_k,
        temperature=args.temperature,
    )

    payload = {
        "prompt": args.prompt,
        "tokenizer": getattr(tokenizer, "name", "unknown"),
        "temperature": args.temperature,
        "top_k": args.top_k,
        "context_token_ids": prompt_ids,
        "context_tokens": [tokenizer.itos[token_id] for token_id in prompt_ids],
        "predictions": [prediction.to_dict() for prediction in predictions],
    }
    json_path = out_dir / "predictions.json"
    svg_path = out_dir / "predictions.svg"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_predictions_svg(predictions, svg_path)

    print(f"tokenizer={payload['tokenizer']}")
    print(f"context_tokens={payload['context_tokens']}")
    print(f"saved_json={json_path}")
    print(f"saved_svg={svg_path}")
    print("predictions=" + json.dumps(payload["predictions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
