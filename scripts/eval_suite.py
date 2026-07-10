from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import torch

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path

ROOT = PROJECT_ROOT
ensure_src_path()

from minigpt.core.model import GPTConfig, MiniGPT  # noqa: E402
from minigpt.core.tokenizer import load_tokenizer  # noqa: E402
from minigpt.evaluation.suite import (  # noqa: E402
    build_eval_suite_report,
    build_prompt_result,
    load_builtin_prompt_suite,
    load_prompt_suite,
    write_eval_suite_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a fixed prompt evaluation suite for a MiniGPT checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--suite", type=Path, default=ROOT / "data" / "eval_prompts.json")
    parser.add_argument("--suite-name", choices=["default", "standard-zh"], default=None, help="Use a built-in prompt suite instead of --suite.")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args(argv)


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


@torch.no_grad()
def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    device = choose_device(args.device)
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"
    out_dir = args.out_dir or args.checkpoint.parent / "eval_suite"

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    suite = load_builtin_prompt_suite(args.suite_name) if args.suite_name else load_prompt_suite(args.suite)
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
        suite=f"builtin:{args.suite_name}" if args.suite_name else str(args.suite),
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
