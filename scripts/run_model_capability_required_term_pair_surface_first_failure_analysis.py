from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_surface_first_failure_analysis import (  # noqa: E402
    build_model_capability_required_term_pair_surface_first_failure_analysis,
    locate_surface_first_alignment_comparison,
    locate_surface_first_forced_choice_report,
    locate_surface_first_refresh_report,
    locate_surface_first_route_decision,
    read_surface_first_analysis_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_first_failure_analysis_artifacts import (  # noqa: E402
    render_surface_first_failure_analysis_text,
    write_surface_first_failure_analysis_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze required-term pair surface-first schedule failure.")
    parser.add_argument("--refresh", type=Path, required=True, help="Surface-first refresh JSON path or output dir.")
    parser.add_argument("--forced-choice", type=Path, required=True, help="Surface-first forced-choice JSON path or output dir.")
    parser.add_argument("--comparison", type=Path, required=True, help="Alignment comparison JSON path or output dir.")
    parser.add_argument("--route-decision", type=Path, required=True, help="Route decision JSON path or output dir.")
    parser.add_argument("--source-label", default="surface-first-schedule")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-surface-first-failure-analysis",
    )
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_surface_first_failure_analysis(
        refresh_report=read_surface_first_analysis_input(locate_surface_first_refresh_report(args.refresh)),
        forced_choice_report=read_surface_first_analysis_input(
            locate_surface_first_forced_choice_report(args.forced_choice)
        ),
        comparison_report=read_surface_first_analysis_input(locate_surface_first_alignment_comparison(args.comparison)),
        route_decision_report=read_surface_first_analysis_input(locate_surface_first_route_decision(args.route_decision)),
        source_label=args.source_label,
    )
    outputs = write_surface_first_failure_analysis_outputs(report, args.out_dir)
    print(render_surface_first_failure_analysis_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
