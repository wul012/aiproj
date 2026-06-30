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

from minigpt.core.dataset import load_text
from minigpt.core.tokenizer import BPETokenizer, CharTokenizer, load_tokenizer


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a MiniGPT tokenizer.")
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "sample_zh.txt")
    parser.add_argument("--tokenizer-path", type=Path, default=None)
    parser.add_argument("--tokenizer", choices=["char", "bpe"], default="char")
    parser.add_argument("--bpe-vocab-size", type=int, default=256)
    parser.add_argument("--bpe-min-frequency", type=int, default=2)
    parser.add_argument("--text", type=str, default="人工智能")
    parser.add_argument("--show-merges", type=int, default=12)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.tokenizer_path is not None:
        tokenizer = load_tokenizer(args.tokenizer_path)
        source = str(args.tokenizer_path)
    else:
        text = load_text(args.data)
        if args.tokenizer == "bpe":
            tokenizer = BPETokenizer.train(
                text,
                vocab_size=args.bpe_vocab_size,
                min_frequency=args.bpe_min_frequency,
            )
        else:
            tokenizer = CharTokenizer.train(text)
        source = str(args.data)

    ids = tokenizer.encode(args.text)
    print(f"source={source}")
    print(f"tokenizer={getattr(tokenizer, 'name', 'unknown')}")
    print(f"vocab_size={tokenizer.vocab_size}")
    print(f"text={args.text}")
    print(f"ids={ids}")
    print(f"decoded={tokenizer.decode(ids)}")

    merges = getattr(tokenizer, "merges", [])
    if merges:
        print(f"merges_count={len(merges)}")
        for i, (left, right) in enumerate(merges[: args.show_merges], start=1):
            print(f"merge_{i}={left!r}+{right!r}->{left + right!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
