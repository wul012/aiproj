from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.eval_suite import load_prompt_suite
from minigpt.pair_batch import build_pair_batch_case_result, build_pair_batch_report, write_pair_batch_outputs
from minigpt.server import GenerationRequest, MiniGPTGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fixed prompts against two MiniGPT checkpoints and save pair-generation reports.")
    parser.add_argument("--left-checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--right-checkpoint", type=Path, required=True)
    parser.add_argument("--left-tokenizer", type=Path, default=None)
    parser.add_argument("--right-tokenizer", type=Path, default=None)
    parser.add_argument("--left-id", type=str, default="left")
    parser.add_argument("--right-id", type=str, default="right")
    parser.add_argument("--suite", type=Path, default=ROOT / "data" / "eval_prompts.json")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    suite = load_prompt_suite(args.suite)
    left_tokenizer = args.left_tokenizer or args.left_checkpoint.parent / "tokenizer.json"
    right_tokenizer = args.right_tokenizer or args.right_checkpoint.parent / "tokenizer.json"
    out_dir = args.out_dir or args.left_checkpoint.parent / "pair_batch"

    left_generator = MiniGPTGenerator(args.left_checkpoint, left_tokenizer, args.device)
    right_generator = MiniGPTGenerator(args.right_checkpoint, right_tokenizer, args.device)
    results = []
    for case in suite.cases:
        left_request = GenerationRequest(
            prompt=case.prompt,
            max_new_tokens=case.max_new_tokens,
            temperature=case.temperature,
            top_k=case.top_k,
            seed=case.seed,
            checkpoint=args.left_id,
        )
        right_request = GenerationRequest(
            prompt=case.prompt,
            max_new_tokens=case.max_new_tokens,
            temperature=case.temperature,
            top_k=case.top_k,
            seed=case.seed,
            checkpoint=args.right_id,
        )
        left_response = left_generator.generate(left_request)
        right_response = right_generator.generate(right_request)
        results.append(
            build_pair_batch_case_result(
                case,
                left_response,
                right_response,
                left_checkpoint_id=args.left_id,
                right_checkpoint_id=args.right_id,
            )
        )

    report = build_pair_batch_report(
        results,
        suite=suite,
        suite_path=args.suite,
        left_checkpoint=args.left_checkpoint,
        right_checkpoint=args.right_checkpoint,
        left_checkpoint_id=args.left_id,
        right_checkpoint_id=args.right_id,
        left_tokenizer=left_tokenizer,
        right_tokenizer=right_tokenizer,
    )
    outputs = write_pair_batch_outputs(report, out_dir)
    print(f"cases={report['case_count']}")
    print(f"suite_name={suite.name}")
    print(f"suite_version={suite.version}")
    print(f"left_checkpoint_id={args.left_id}")
    print(f"right_checkpoint_id={args.right_id}")
    print(f"generated_equal_count={report['generated_equal_count']}")
    print(f"generated_difference_count={report['generated_difference_count']}")
    print(f"avg_abs_generated_char_delta={report['avg_abs_generated_char_delta']}")
    print(f"out_dir={out_dir}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
