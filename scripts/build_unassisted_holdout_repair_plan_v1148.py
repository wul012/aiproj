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
from minigpt.unassisted_holdout_repair_plan_v1148 import (  # noqa: E402
    build_unassisted_holdout_repair_plan_v1148,
    default_v1147_comparison_path,
    locate_v1147_comparison,
    read_json_report,
    resolve_exit_code,
    write_unassisted_holdout_repair_plan_v1148_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build v1148 unassisted holdout repair plan from the v1147 comparison report.")
    parser.add_argument("--comparison", type=Path, default=default_v1147_comparison_path(ROOT), help="v1147 comparison JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "unassisted-holdout-repair-plan-v1148")
    parser.add_argument("--require-plan-ready", action="store_true", help="Return 1 if the repair plan inputs are not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    comparison_path = locate_v1147_comparison(args.comparison)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_unassisted_holdout_repair_plan_v1148(
        read_json_report(comparison_path, description="v1147 decoder-anchor holdout comparison"),
        comparison_path=comparison_path,
    )
    outputs = write_unassisted_holdout_repair_plan_v1148_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
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
