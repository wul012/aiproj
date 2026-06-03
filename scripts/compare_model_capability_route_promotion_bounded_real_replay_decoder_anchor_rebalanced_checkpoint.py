from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison,
    locate_rebalanced_training_run,
    locate_route_promotion_bounded_real_replay,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare bounded replay for baseline, prompt-aligned, decoder-anchor, and rebalanced checkpoints.")
    parser.add_argument("--baseline-replay", type=Path, required=True)
    parser.add_argument("--prompt-aligned-replay", type=Path, required=True)
    parser.add_argument("--decoder-anchor-replay", type=Path, required=True)
    parser.add_argument("--rebalanced-replay", type=Path, required=True)
    parser.add_argument("--rebalanced-training", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison")
    parser.add_argument("--require-comparison-pass", action="store_true")
    parser.add_argument("--require-improvement", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    baseline_path = locate_route_promotion_bounded_real_replay(args.baseline_replay)
    prompt_path = locate_route_promotion_bounded_real_replay(args.prompt_aligned_replay)
    decoder_path = locate_route_promotion_bounded_real_replay(args.decoder_anchor_replay)
    rebalanced_path = locate_route_promotion_bounded_real_replay(args.rebalanced_replay)
    training_path = locate_rebalanced_training_run(args.rebalanced_training) if args.rebalanced_training else None
    prepare_output_dir(args.out_dir, force=args.force, preserve_paths=[baseline_path, prompt_path, decoder_path, rebalanced_path, training_path])
    report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison(
        read_json_report(baseline_path),
        read_json_report(prompt_path),
        read_json_report(decoder_path),
        read_json_report(rebalanced_path),
        read_json_report(training_path) if training_path else None,
        baseline_replay_path=baseline_path,
        prompt_aligned_replay_path=prompt_path,
        decoder_anchor_replay_path=decoder_path,
        rebalanced_replay_path=rebalanced_path,
        rebalanced_training_path=training_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(report, require_comparison_ready=args.require_comparison_pass, require_improvement=args.require_improvement)
    if code:
        raise SystemExit(code)


def prepare_output_dir(out_dir: Path, *, force: bool, preserve_paths: list[Path | None]) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        preserved = _preserved_children(out_dir, preserve_paths)
        if preserved:
            for child in out_dir.iterdir():
                if child.resolve() in preserved:
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        else:
            shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def _preserved_children(out_dir: Path, paths: list[Path | None]) -> set[Path]:
    preserved: set[Path] = set()
    root = out_dir.resolve()
    for path in paths:
        if path is None:
            continue
        candidate = path.resolve()
        if candidate.is_file():
            candidate = candidate.parent
        try:
            relative = candidate.relative_to(root)
        except ValueError:
            continue
        if relative.parts:
            preserved.add(root / relative.parts[0])
    return preserved


if __name__ == "__main__":
    main()
