from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.eval_suite import build_eval_suite_report, build_prompt_result, load_prompt_suite, write_eval_suite_outputs
from minigpt.model import GPTConfig, MiniGPT
from minigpt.tokenizer import load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a fixed prompt evaluation suite for a MiniGPT checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--suite", type=Path, default=ROOT / "data" / "eval_prompts.json")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


@torch.no_grad()
def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"
    out_dir = args.out_dir or args.checkpoint.parent / "eval_suite"

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    suite = load_prompt_suite(args.suite)
    cases = list(suite.cases)
    results = []
    for case in cases:
        torch.manual_seed(case.seed)
        prompt_ids = tokenizer.encode(case.prompt)
        idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
        out = model.generate(
            idx,
            max_new_tokens=case.max_new_tokens,
            temperature=case.temperature,
            top_k=case.top_k,
        )
        generated = tokenizer.decode(out[0].tolist())
        results.append(build_prompt_result(case, generated))

    report = build_eval_suite_report(
        results,
        checkpoint=str(args.checkpoint),
        tokenizer=str(tokenizer_path),
        suite=str(args.suite),
        suite_name=suite.name,
        suite_version=suite.version,
        suite_description=suite.description,
        suite_language=suite.language,
    )
    outputs = write_eval_suite_outputs(report, out_dir)
    print(f"cases={len(results)}")
    print(f"suite_name={suite.name}")
    print(f"suite_version={suite.version}")
    print("task_types=" + ",".join(report["task_type_counts"]))
    print(f"out_dir={out_dir}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
