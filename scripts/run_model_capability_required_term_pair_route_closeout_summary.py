from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_route_closeout_summary import (  # noqa: E402
    build_model_capability_required_term_pair_route_closeout_summary,
    locate_fresh_seed_report,
    locate_fresh_seed_route_decision_report,
    locate_heldout_replay_report,
    locate_route_comparison_report,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_route_closeout_summary_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_route_closeout_summary_text,
    write_model_capability_required_term_pair_route_closeout_summary_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize the required-term pair route closeout evidence.")
    parser.add_argument("--heldout", type=Path, required=True, help="Held-out replay JSON file or output directory.")
    parser.add_argument(
        "--fresh-seed",
        nargs=2,
        action="append",
        metavar=("LABEL", "PATH"),
        default=[],
        help="Fresh-seed stability label and JSON file/output directory. Repeatable.",
    )
    parser.add_argument("--comparison", type=Path, required=True, help="Route comparison JSON file or output directory.")
    parser.add_argument("--decision", type=Path, required=True, help="Route decision JSON file or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-route-closeout-summary")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the closeout summary is not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    heldout_path = locate_heldout_replay_report(args.heldout)
    fresh_pairs = [(str(label), locate_fresh_seed_report(path)) for label, path in args.fresh_seed]
    comparison_path = locate_route_comparison_report(args.comparison)
    decision_path = locate_fresh_seed_route_decision_report(args.decision)
    report = build_model_capability_required_term_pair_route_closeout_summary(
        heldout_report=read_json_report(heldout_path),
        fresh_seed_reports=[read_json_report(path) for _, path in fresh_pairs],
        comparison_report=read_json_report(comparison_path),
        route_decision_report=read_json_report(decision_path),
        heldout_path=heldout_path,
        fresh_seed_paths=[path for _, path in fresh_pairs],
        fresh_seed_labels=[label for label, _ in fresh_pairs],
        comparison_path=comparison_path,
        route_decision_path=decision_path,
    )
    outputs = write_model_capability_required_term_pair_route_closeout_summary_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_route_closeout_summary_text(report), end="")
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
