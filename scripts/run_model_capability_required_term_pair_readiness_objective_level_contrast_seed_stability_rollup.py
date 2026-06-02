from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup import (  # noqa: E402
    build_objective_level_contrast_seed_stability_rollup,
    locate_seed_stability_rollup_plan,
    locate_seed_stability_rollup_replay,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup_artifacts import (  # noqa: E402
    render_objective_level_contrast_seed_stability_rollup_text,
    write_objective_level_contrast_seed_stability_rollup_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Roll up objective-level contrast seed stability replay evidence.")
    parser.add_argument("--plan", type=Path, required=True, help="Seed stability plan JSON or output directory.")
    parser.add_argument("--replay", action="append", default=[], help="Replay report as seed=path. Repeat for each seed.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-objective-level-contrast-seed-stability-rollup")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when rollup checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if not args.replay:
        raise SystemExit("at least one --replay seed=path is required")
    plan_source = locate_seed_stability_rollup_plan(args.plan)
    replay_inputs = [_parse_replay_spec(item) for item in args.replay]
    replay_reports = []
    for seed, replay_path in replay_inputs:
        source = locate_seed_stability_rollup_replay(replay_path)
        replay_reports.append((seed, read_json_report(source), source))
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_objective_level_contrast_seed_stability_rollup(
        read_json_report(plan_source),
        replay_reports,
        source_plan_path=plan_source,
    )
    outputs = write_objective_level_contrast_seed_stability_rollup_outputs(report, args.out_dir)
    print(render_objective_level_contrast_seed_stability_rollup_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def _parse_replay_spec(value: str) -> tuple[int, Path]:
    if "=" not in value:
        raise SystemExit(f"invalid --replay value, expected seed=path: {value}")
    seed_text, raw_path = value.split("=", 1)
    try:
        seed = int(seed_text)
    except ValueError as exc:
        raise SystemExit(f"invalid replay seed: {seed_text}") from exc
    return seed, Path(raw_path)


if __name__ == "__main__":
    main()
