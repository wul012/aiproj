from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model import GPTConfig, MiniGPT
from minigpt.sampling import (
    build_sampling_report,
    build_sampling_result,
    default_sampling_cases,
    parse_sampling_case,
    write_sampling_outputs,
)
from minigpt.tokenizer import load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare MiniGPT generation under different sampling settings.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--prompt", type=str, default="人工智能")
    parser.add_argument("--max-new-tokens", type=int, default=80)
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Sampling case as name:temperature:top_k:seed. Use top_k=0 for no top-k filter.",
    )
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
    if args.max_new_tokens < 1:
        raise ValueError("--max-new-tokens must be at least 1")

    device = choose_device(args.device)
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"
    out_dir = args.out_dir or args.checkpoint.parent / "sample_lab"
    cases = [parse_sampling_case(spec) for spec in args.case] if args.case else default_sampling_cases()

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    prompt_ids = tokenizer.encode(args.prompt)
    if not prompt_ids:
        raise ValueError("Prompt produced no token ids")
    if len(prompt_ids) > config.block_size:
        prompt_ids = prompt_ids[-config.block_size :]
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)

    results = []
    for case in cases:
        torch.manual_seed(case.seed)
        if device.type == "cuda":
            torch.cuda.manual_seed_all(case.seed)
        with torch.no_grad():
            out = model.generate(
                idx.clone(),
                max_new_tokens=args.max_new_tokens,
                temperature=case.temperature,
                top_k=case.top_k,
            )
        generated = tokenizer.decode(out[0].tolist())
        results.append(build_sampling_result(case, args.prompt, args.max_new_tokens, generated))

    report = build_sampling_report(
        prompt=args.prompt,
        max_new_tokens=args.max_new_tokens,
        results=results,
        checkpoint=str(args.checkpoint),
        tokenizer=getattr(tokenizer, "name", "unknown"),
    )
    outputs = write_sampling_outputs(report, out_dir)

    print(f"prompt={args.prompt}")
    print(f"cases={len(results)}")
    print("results=" + json.dumps([result.to_dict() for result in results], ensure_ascii=False))
    for key, path in outputs.items():
        print(f"saved_{key}={path}")


if __name__ == "__main__":
    main()
