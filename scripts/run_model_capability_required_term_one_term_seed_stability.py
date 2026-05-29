from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_one_term_seed_stability import (  # noqa: E402
    build_model_capability_required_term_one_term_seed_stability,
    locate_model_capability_required_term_one_term_seed_stability_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_one_term_seed_stability_artifacts import (  # noqa: E402
    render_model_capability_required_term_one_term_seed_stability_text,
    write_model_capability_required_term_one_term_seed_stability_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repeat v492 successful one-term required-term runs across seeds."
    )
    parser.add_argument("one_term_isolation", type=Path, help="Path to v492 one-term isolation JSON or directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-one-term-seed-stability",
    )
    parser.add_argument("--seeds", default="493,1493,2493", help="Comma-separated training/generation seeds.")
    parser.add_argument("--include-all-terms", action="store_true", help="Include v492 miss terms instead of hit terms only.")
    parser.add_argument("--term-limit", type=int, default=None)
    parser.add_argument("--repeat", type=int, default=200)
    parser.add_argument("--max-iters", type=int, default=1200)
    parser.add_argument("--eval-iters", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-head", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.02)
    parser.add_argument("--max-new-tokens", type=int, default=12)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the report fails structurally.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_model_capability_required_term_one_term_seed_stability_source(args.one_term_isolation)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_one_term_seed_stability(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        seeds=parse_seeds(args.seeds),
        include_all_terms=args.include_all_terms,
        term_limit=args.term_limit,
        repeat=args.repeat,
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
        device=args.device,
    )
    outputs = write_model_capability_required_term_one_term_seed_stability_outputs(report, args.out_dir)
    print(render_model_capability_required_term_one_term_seed_stability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def parse_seeds(value: str) -> tuple[int, ...]:
    seeds: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        seed = int(item)
        if seed not in seeds:
            seeds.append(seed)
    if not seeds:
        raise SystemExit("--seeds must include at least one integer seed")
    return tuple(seeds)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
