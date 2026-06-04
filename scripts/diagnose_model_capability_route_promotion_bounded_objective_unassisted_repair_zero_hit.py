from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic import (  # noqa: E402
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic,
    locate_unassisted_repair_replay_comparison,
    locate_unassisted_repair_seed,
    locate_unassisted_repair_training_run,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic_artifacts import (  # noqa: E402
    render_bounded_objective_unassisted_repair_zero_hit_diagnostic_text,
    write_bounded_objective_unassisted_repair_zero_hit_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose bounded objective unassisted repair replay zero-hit failures.")
    parser.add_argument("--replay-comparison", type=Path, required=True)
    parser.add_argument("--unassisted-repair-seed", type=Path, required=True)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-objective-unassisted-repair-zero-hit-diagnostic")
    parser.add_argument("--require-diagnostic-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_unassisted_repair_replay_comparison(args.replay_comparison)
    seed_path = locate_unassisted_repair_seed(args.unassisted_repair_seed)
    training_path = locate_unassisted_repair_training_run(args.training_run)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic(
        read_json_report(replay_path),
        read_json_report(seed_path),
        read_json_report(training_path),
        corpus_path=args.corpus,
        replay_comparison_path=replay_path,
        unassisted_repair_seed_path=seed_path,
        unassisted_repair_training_run_path=training_path,
    )
    outputs = write_bounded_objective_unassisted_repair_zero_hit_diagnostic_outputs(report, args.out_dir)
    print(render_bounded_objective_unassisted_repair_zero_hit_diagnostic_text(report), end="")
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
