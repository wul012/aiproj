from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic,
    locate_prompt_aligned_comparison,
    locate_prompt_aligned_replay,
    locate_prompt_aligned_seed_revision,
    locate_prompt_aligned_training_run,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_text,
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose why a prompt-aligned bounded replay checkpoint still failed.")
    parser.add_argument("--prompt-aligned-replay", type=Path, required=True, help="Prompt-aligned bounded replay JSON or output directory.")
    parser.add_argument("--comparison", type=Path, required=True, help="Prompt-aligned checkpoint comparison JSON or output directory.")
    parser.add_argument("--prompt-aligned-seed", type=Path, required=True, help="Prompt-aligned seed revision JSON or output directory.")
    parser.add_argument("--training-run", type=Path, required=True, help="Prompt-aligned training run evidence JSON or output directory.")
    parser.add_argument("--corpus", type=Path, required=True, help="Prompt-aligned corpus text file.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-prompt-aligned-failure-diagnostic")
    parser.add_argument("--require-diagnostic-ready", action="store_true", help="Return exit code 1 when diagnostic inputs are not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_prompt_aligned_replay(args.prompt_aligned_replay)
    comparison_path = locate_prompt_aligned_comparison(args.comparison)
    seed_path = locate_prompt_aligned_seed_revision(args.prompt_aligned_seed)
    training_path = locate_prompt_aligned_training_run(args.training_run)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic(
        read_json_report(replay_path),
        read_json_report(comparison_path),
        read_json_report(seed_path),
        read_json_report(training_path),
        corpus_path=args.corpus,
        replay_path=replay_path,
        comparison_path=comparison_path,
        seed_revision_path=seed_path,
        training_run_path=training_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_diagnostic_ready=args.require_diagnostic_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
