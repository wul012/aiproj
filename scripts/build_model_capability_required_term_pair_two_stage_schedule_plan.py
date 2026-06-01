from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_two_stage_schedule_plan import (  # noqa: E402
    build_model_capability_required_term_pair_two_stage_schedule_plan,
    locate_two_stage_schedule_forced_choice_report,
    locate_two_stage_schedule_refresh_report,
    make_two_stage_schedule_plan_source,
    read_two_stage_schedule_plan_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_two_stage_schedule_plan_artifacts import (  # noqa: E402
    render_two_stage_schedule_plan_text,
    write_two_stage_schedule_plan_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a required-term pair two-stage schedule plan.")
    parser.add_argument(
        "--surface-source",
        nargs=3,
        metavar=("LABEL", "REFRESH_REPORT", "FORCED_CHOICE_REPORT"),
        required=True,
        help="Surface route label, refresh report JSON/dir, and forced-choice diagnostic JSON/dir.",
    )
    parser.add_argument(
        "--internal-source",
        nargs=3,
        metavar=("LABEL", "REFRESH_REPORT", "FORCED_CHOICE_REPORT"),
        required=True,
        help="Internal route label, refresh report JSON/dir, and forced-choice diagnostic JSON/dir.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-two-stage-schedule-plan",
    )
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    surface = _source_from_args(args.surface_source)
    internal = _source_from_args(args.internal_source)
    report = build_model_capability_required_term_pair_two_stage_schedule_plan(
        surface_source=surface,
        internal_source=internal,
    )
    outputs = write_two_stage_schedule_plan_outputs(report, args.out_dir)
    print(render_two_stage_schedule_plan_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def _source_from_args(values: Sequence[str]) -> dict[str, object]:
    label, refresh_input, forced_input = values
    refresh_path = locate_two_stage_schedule_refresh_report(refresh_input)
    forced_path = locate_two_stage_schedule_forced_choice_report(forced_input)
    return make_two_stage_schedule_plan_source(
        label=label,
        refresh_report=read_two_stage_schedule_plan_input(refresh_path),
        forced_choice_report=read_two_stage_schedule_plan_input(forced_path),
        refresh_path=refresh_path,
        forced_choice_path=forced_path,
    )


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
