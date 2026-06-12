from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402
from minigpt.unassisted_loss_suffix_repair_replay_comparison_v1155 import (  # noqa: E402
    build_unassisted_loss_suffix_repair_replay_comparison_v1155,
    default_v1154_training_handoff_path,
    locate_v1154_training_handoff,
    read_json_report,
    read_json_rows,
    resolve_exit_code,
    write_unassisted_loss_suffix_repair_replay_comparison_v1155_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay v1153 target-free holdout prompts against the v1154 repair checkpoint.")
    parser.add_argument("--handoff", type=Path, default=default_v1154_training_handoff_path(ROOT), help="v1154 training handoff JSON or output directory.")
    parser.add_argument("--holdout-prompts", type=Path, default=None, help="Optional holdout prompts JSON override.")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Optional checkpoint override.")
    parser.add_argument("--tokenizer", type=Path, default=None, help="Optional tokenizer override.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--precomputed-generations", type=Path, default=None, help="Optional JSON generation rows for tests or offline replay review.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "unassisted-loss-suffix-repair-replay-comparison-v1155")
    parser.add_argument("--require-comparison-ready", action="store_true")
    parser.add_argument("--require-full-pair", action="store_true")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    handoff_path = locate_v1154_training_handoff(args.handoff)
    prepare_output_dir(args.out_dir, force=args.force)
    handoff = read_json_report(handoff_path, description="v1154 unassisted loss suffix repair training handoff")
    holdout_prompts = read_json_rows(args.holdout_prompts, description="v1153 target-free holdout prompts") if args.holdout_prompts is not None else None
    generations = read_json_rows(args.precomputed_generations, description="precomputed generation rows") if args.precomputed_generations is not None else None
    report = build_unassisted_loss_suffix_repair_replay_comparison_v1155(
        handoff,
        holdout_prompts=holdout_prompts,
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        handoff_path=handoff_path,
        precomputed_generations=generations,
    )
    outputs = write_unassisted_loss_suffix_repair_replay_comparison_v1155_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(report, require_comparison_ready=args.require_comparison_ready, require_full_pair=args.require_full_pair)
    if code:
        raise SystemExit(code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
