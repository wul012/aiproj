from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_portfolio_batch import (  # noqa: E402
    build_training_portfolio_batch_plan,
    load_training_portfolio_batch_variants,
    run_training_portfolio_batch_plan,
    write_training_portfolio_batch_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or run a batch of MiniGPT training portfolio variants.")
    parser.add_argument("sources", nargs="+", type=Path, help="Training text files or directories")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--out-root", type=Path, default=ROOT / "runs" / "training-portfolio-batch")
    parser.add_argument("--variants", type=Path, default=None, help="Optional JSON list or {variants:[...]} matrix")
    parser.add_argument("--dataset-name", type=str, default="portfolio-zh")
    parser.add_argument("--dataset-description", type=str, default="MiniGPT training portfolio batch dataset.")
    parser.add_argument("--suite", type=Path, default=ROOT / "data" / "eval_prompts.json")
    parser.add_argument("--request-log", type=Path, default=None, help="Optional inference_requests.jsonl to summarize")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--max-iters", type=int, default=100)
    parser.add_argument("--eval-interval", type=int, default=25)
    parser.add_argument("--eval-iters", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--block-size", type=int, default=64)
    parser.add_argument("--n-layer", type=int, default=2)
    parser.add_argument("--n-head", type=int, default=2)
    parser.add_argument("--n-embd", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--sample-prompt", type=str, default="MiniGPT")
    parser.add_argument("--sample-tokens", type=int, default=40)
    parser.add_argument("--baseline", type=str, default=None, help="Baseline variant name; defaults to the first variant")
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--title", type=str, default="MiniGPT training portfolio batch")
    parser.add_argument("--execute", action="store_true", help="Actually run each portfolio variant. Omit for dry-run planning.")
    parser.add_argument("--no-compare", action="store_true", help="Skip the automatic comparison report after variant reports are written.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    variants = load_training_portfolio_batch_variants(args.variants) if args.variants else None
    plan = build_training_portfolio_batch_plan(
        args.project_root,
        args.sources,
        out_root=args.out_root,
        variants=variants,
        dataset_name=args.dataset_name,
        dataset_description=args.dataset_description,
        suite_path=args.suite,
        request_log_path=args.request_log,
        python_executable=args.python,
        device=args.device,
        max_iters=args.max_iters,
        eval_interval=args.eval_interval,
        eval_iters=args.eval_iters,
        batch_size=args.batch_size,
        block_size=args.block_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd,
        learning_rate=args.learning_rate,
        seed=args.seed,
        sample_prompt=args.sample_prompt,
        sample_tokens=args.sample_tokens,
        baseline=args.baseline,
        title=args.title,
    )
    report = run_training_portfolio_batch_plan(plan, execute=args.execute, compare=not args.no_compare)
    outputs = write_training_portfolio_batch_outputs(report, args.out_root)
    execution = report["execution"]
    print(f"status={execution.get('status')}")
    print(f"execute={execution.get('execute')}")
    print(f"variant_count={execution.get('variant_count')}")
    print(f"completed_variants={execution.get('completed_variant_count')}")
    print(f"failed_variant={execution.get('failed_variant')}")
    print(f"comparison_status={execution.get('comparison_status')}")
    print("summary=" + json.dumps(report.get("summary", {}), ensure_ascii=False))
    print("comparison_outputs=" + json.dumps(report.get("comparison_outputs", {}), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if execution.get("status") == "failed" or execution.get("comparison_status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
