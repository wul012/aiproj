from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_capacity_sweep import (  # noqa: E402
    build_model_capability_required_term_pair_capacity_sweep,
    default_pair_capacity_sweep_variants,
    locate_model_capability_required_term_pair_capacity_sweep_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_capacity_sweep_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_capacity_sweep_text,
    write_model_capability_required_term_pair_capacity_sweep_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sweep capacity variants for fragile v496 pair-rebalance targets.")
    parser.add_argument("pair_seed_stability", type=Path, help="Path to v496 seed-stability JSON or directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-capacity-sweep",
    )
    parser.add_argument("--seed", type=int, default=496, help="Training/generation seed for each capacity variant.")
    parser.add_argument("--pair-limit", type=int, default=1)
    parser.add_argument(
        "--variant-preset",
        choices=("default", "fast"),
        default="default",
        help="default runs 4 variants; fast keeps only the baseline-repeat variant.",
    )
    parser.add_argument("--eval-iters", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--max-new-tokens", type=int, default=12)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the report fails structurally.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_model_capability_required_term_pair_capacity_sweep_source(args.pair_seed_stability)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_capacity_sweep(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        seed=args.seed,
        pair_limit=args.pair_limit,
        capacity_variants=capacity_variants(args.variant_preset),
        eval_iters=args.eval_iters,
        batch_size=args.batch_size,
        block_size=args.block_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_capacity_sweep_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_capacity_sweep_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def capacity_variants(preset: str) -> list[dict[str, object]]:
    variants = default_pair_capacity_sweep_variants()
    if preset == "fast":
        return variants[:1]
    return variants


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
