"""v1161: verify KV-cache correctness and benchmark generation speedup.

Example:
    python scripts/run_kv_cache_eval_v1161.py --device auto --max-new-tokens 200
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

from minigpt.kv_cache_eval_v1161 import KvCacheBenchConfig, run_kv_cache_benchmark  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "kv_cache_eval_v1161"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify and benchmark KV-cached generation.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "kv-cache-eval-v1161")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--block-size", type=int, default=256)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--vocab-size", type=int, default=64)
    parser.add_argument("--prompt-len", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=200)
    parser.add_argument("--no-rope", action="store_true")
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
    device = choose_device(args.device)

    config = KvCacheBenchConfig(
        vocab_size=args.vocab_size, block_size=args.block_size, n_layer=args.n_layer, n_head=args.n_head,
        n_embd=args.n_embd, prompt_len=args.prompt_len, max_new_tokens=args.max_new_tokens, seed=args.seed,
        use_rope=not args.no_rope,
    )
    report = run_kv_cache_benchmark(config=config, device=device)

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
