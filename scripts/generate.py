from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

from minigpt.serving.contracts import GenerationRequest, parse_generation_request
from minigpt.serving.generator import MiniGPTGenerator
from minigpt.serving.profiles import generation_profile_ids


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
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
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
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
    return 0


def _generate(checkpoint: Path, tokenizer: Path, device: str, request: GenerationRequest) -> str:
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).generated


if __name__ == "__main__":
    raise SystemExit(main())
