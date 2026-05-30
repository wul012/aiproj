from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare import (  # noqa: E402
    build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare,
    locate_loss_alias_blocked_token_fresh_compare_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_text,
    write_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fresh-train a loss-alias focus checkpoint and compare blocked-token decoding.")
    parser.add_argument("stability", type=Path, help="v515 loss-alias stability JSON or output directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-loss-alias-blocked-token-fresh-compare",
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[527])
    parser.add_argument("--base-repeat", type=int, default=180)
    parser.add_argument("--focus-repeat", type=int, default=180)
    parser.add_argument("--bridge-repeat", type=int, default=4)
    parser.add_argument("--max-iters", type=int, default=900)
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
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the comparison fails structurally.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source = locate_loss_alias_blocked_token_fresh_compare_source(args.stability)
    report = build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        seeds=args.seeds,
        base_repeat=args.base_repeat,
        focus_repeat=args.focus_repeat,
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
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare_text(report), end="")
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
