from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison,
    locate_repair_training_run,
    locate_route_promotion_bounded_real_replay,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare a bounded real replay baseline with a repair checkpoint replay.")
    parser.add_argument("--baseline-replay", type=Path, required=True, help="Baseline bounded real replay JSON or output directory.")
    parser.add_argument("--repair-replay", type=Path, required=True, help="Repair checkpoint bounded real replay JSON or output directory.")
    parser.add_argument("--training-evidence", type=Path, default=None, help="Optional repair training evidence JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-repair-checkpoint-comparison")
    parser.add_argument("--require-comparison-pass", action="store_true", help="Return exit code 1 when comparison inputs are invalid.")
    parser.add_argument("--require-improvement", action="store_true", help="Return exit code 1 unless the repair checkpoint improves over baseline.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    baseline_path = locate_route_promotion_bounded_real_replay(args.baseline_replay)
    repair_path = locate_route_promotion_bounded_real_replay(args.repair_replay)
    training_path = locate_repair_training_run(args.training_evidence) if args.training_evidence else None
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison(
        read_json_report(baseline_path),
        read_json_report(repair_path),
        read_json_report(training_path) if training_path else None,
        baseline_replay_path=baseline_path,
        repair_replay_path=repair_path,
        training_run_path=training_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_comparison_ready=args.require_comparison_pass,
        require_improvement=args.require_improvement,
    )
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
