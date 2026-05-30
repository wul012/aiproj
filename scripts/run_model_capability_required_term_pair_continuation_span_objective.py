from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_continuation_span_objective import (  # noqa: E402
    build_model_capability_required_term_pair_continuation_span_objective,
    locate_model_capability_required_term_pair_continuation_span_objective_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_continuation_span_objective_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_continuation_span_objective_text,
    write_model_capability_required_term_pair_continuation_span_objective_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a fixed/loss continuation-span objective experiment from the v509 rollup.")
    parser.add_argument("rollup", type=Path, help="v509 diagnostic rollup JSON or output directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-continuation-span-objective",
    )
    parser.add_argument("--repeat", type=int, default=160)
    parser.add_argument("--bridge-repeat", type=int, default=4)
    parser.add_argument("--max-iters", type=int, default=800)
    parser.add_argument("--eval-iters", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--block-size", type=int, default=16)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.02)
    parser.add_argument("--max-new-tokens", type=int, default=12)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--seed", type=int, default=510)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the report fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source = locate_model_capability_required_term_pair_continuation_span_objective_source(args.rollup)
    report = build_model_capability_required_term_pair_continuation_span_objective(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        repeat=args.repeat,
        bridge_repeat=args.bridge_repeat,
        max_iters=args.max_iters,
        eval_iters=args.eval_iters,
        batch_size=args.batch_size,
        block_size=args.block_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd,
        learning_rate=args.learning_rate,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        generation_seed=args.seed,
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_continuation_span_objective_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_continuation_span_objective_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
