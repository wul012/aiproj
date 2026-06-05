from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan import (  # noqa: E402
    build_stagnation_aware_suffix_repair_plan,
    locate_stagnation_diagnostic,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_artifacts import (  # noqa: E402
    render_stagnation_aware_suffix_repair_plan_text,
    write_stagnation_aware_suffix_repair_plan_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a stagnation-aware suffix repair plan from a replay stagnation diagnostic.")
    parser.add_argument("--stagnation-diagnostic", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-stagnation-aware-suffix-repair-plan")
    parser.add_argument("--require-plan-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    diagnostic_path = locate_stagnation_diagnostic(args.stagnation_diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_stagnation_aware_suffix_repair_plan(
        read_json_report(diagnostic_path),
        stagnation_diagnostic_path=diagnostic_path,
    )
    outputs = write_stagnation_aware_suffix_repair_plan_outputs(report, args.out_dir)
    print(render_stagnation_aware_suffix_repair_plan_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_plan_ready=args.require_plan_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
