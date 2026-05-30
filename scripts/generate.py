from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.generation_profiles import generation_profile_ids
from minigpt.server_contracts import GenerationRequest, parse_generation_request
from minigpt.server_generator import MiniGPTGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate text with a trained MiniGPT checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--prompt", type=str, default="人工智能")
    parser.add_argument("--max-new-tokens", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--generation-profile", choices=generation_profile_ids(), default="default")
    parser.add_argument("--blocked-token-text", action="append", default=[], help="Additional token text substring to block during decoding.")
    parser.add_argument("--out", type=Path, default=None, help="Optional file path for generated text")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"
    request = parse_generation_request(
        {
            "prompt": args.prompt,
            "max_new_tokens": args.max_new_tokens,
            "temperature": args.temperature,
            "top_k": args.top_k,
            "seed": args.seed,
            "generation_profile": args.generation_profile,
            "blocked_token_texts": args.blocked_token_text,
        }
    )
    generated = _generate(args.checkpoint, tokenizer_path, args.device, request)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(generated, encoding="utf-8")
        print(f"saved={args.out}")
    else:
        print(generated)


def _generate(checkpoint: Path, tokenizer: Path, device: str, request: GenerationRequest) -> str:
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).generated


if __name__ == "__main__":
    main()
