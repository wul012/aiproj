from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_portfolio import (  # noqa: E402
    build_training_portfolio_plan,
    run_training_portfolio_plan,
    write_training_portfolio_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or plan a MiniGPT training portfolio pipeline.")
    parser.add_argument("sources", nargs="+", type=Path, help="Training text files or directories")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--out-root", type=Path, default=ROOT / "runs" / "training-portfolio")
    parser.add_argument("--run-name", type=str, default="portfolio-run")
    parser.add_argument("--dataset-name", type=str, default="portfolio-zh")
    parser.add_argument("--dataset-version", type=str, default="v1")
    parser.add_argument("--dataset-description", type=str, default="MiniGPT training portfolio dataset.")
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
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--title", type=str, default="MiniGPT training portfolio pipeline")
    parser.add_argument("--execute", action="store_true", help="Actually run the pipeline. Omit for dry-run planning.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan = build_training_portfolio_plan(
        args.project_root,
        args.sources,
        out_root=args.out_root,
        run_name=args.run_name,
        dataset_name=args.dataset_name,
        dataset_version=args.dataset_version,
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
        title=args.title,
    )
    report = run_training_portfolio_plan(plan, execute=args.execute)
    outputs = write_training_portfolio_outputs(report, args.out_root)
    execution = report["execution"]
    print(f"status={execution.get('status')}")
    print(f"execute={execution.get('execute')}")
    print(f"step_count={execution.get('step_count')}")
    print(f"completed_steps={execution.get('completed_steps')}")
    print(f"failed_step={execution.get('failed_step')}")
    print(f"available_artifacts={execution.get('available_artifact_count')}/{execution.get('artifact_count')}")
    print("artifacts=" + json.dumps(report.get("artifacts", {}), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if execution.get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
