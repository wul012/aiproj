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
from minigpt.unassisted_holdout_repair_seed_corpus_v1149 import (  # noqa: E402
    build_unassisted_holdout_repair_seed_corpus_v1149,
    default_v1148_plan_path,
    load_seed_blueprint,
    locate_v1148_plan,
    read_json_report,
    resolve_exit_code,
    write_unassisted_holdout_repair_seed_corpus_v1149_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize v1149 unassisted holdout repair seed corpus from the v1148 plan.")
    parser.add_argument("--plan", type=Path, default=default_v1148_plan_path(ROOT), help="v1148 plan JSON or output directory.")
    parser.add_argument("--seed-blueprint", type=Path, default=None, help="Optional seed blueprint JSON override.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "unassisted-holdout-repair-seed-corpus-v1149")
    parser.add_argument("--require-seed-ready", action="store_true", help="Return 1 if corpus materialization is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    plan_path = locate_v1148_plan(args.plan)
    prepare_output_dir(args.out_dir, force=args.force)
    plan = read_json_report(plan_path, description="v1148 unassisted holdout repair plan")
    seed_rows = load_seed_blueprint(plan, plan_path=plan_path, blueprint_path=args.seed_blueprint)
    report = build_unassisted_holdout_repair_seed_corpus_v1149(plan, seed_rows, plan_path=plan_path)
    outputs = write_unassisted_holdout_repair_seed_corpus_v1149_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_seed_ready=args.require_seed_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
