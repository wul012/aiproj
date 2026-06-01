from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_fixed_retention_batch_closeout import (  # noqa: E402
    build_model_capability_required_term_pair_fixed_retention_batch_closeout,
    locate_fixed_retention_comparison_report,
    locate_fixed_retention_refresh_report,
    locate_fixed_retention_route_decision_report,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_fixed_retention_batch_closeout_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_fixed_retention_batch_closeout_text,
    write_model_capability_required_term_pair_fixed_retention_batch_closeout_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close out the required-term pair fixed-retention/loss-rebalance batch.")
    parser.add_argument("--initial-report", type=Path, action="append", required=True, help="Initial fixed-retention refresh JSON or output directory.")
    parser.add_argument("--loss-rebalance-report", type=Path, action="append", required=True, help="Loss-rebalance refresh JSON or output directory.")
    parser.add_argument("--comparison", type=Path, required=True, help="Fixed-retention comparison JSON or output directory.")
    parser.add_argument("--route-decision", type=Path, required=True, help="Fixed-retention route decision JSON or output directory.")
    parser.add_argument("--initial-label", action="append", default=[], help="Optional label for each initial report.")
    parser.add_argument("--loss-rebalance-label", action="append", default=[], help="Optional label for each loss-rebalance report.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-fixed-retention-batch-closeout")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when closeout is not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    initial_paths = [locate_fixed_retention_refresh_report(path) for path in args.initial_report]
    loss_paths = [locate_fixed_retention_refresh_report(path) for path in args.loss_rebalance_report]
    comparison_path = locate_fixed_retention_comparison_report(args.comparison)
    route_decision_path = locate_fixed_retention_route_decision_report(args.route_decision)
    report = build_model_capability_required_term_pair_fixed_retention_batch_closeout(
        initial_reports=[read_json_report(path) for path in initial_paths],
        loss_rebalance_reports=[read_json_report(path) for path in loss_paths],
        comparison_report=read_json_report(comparison_path),
        route_decision_report=read_json_report(route_decision_path),
        initial_paths=initial_paths,
        loss_rebalance_paths=loss_paths,
        comparison_path=comparison_path,
        route_decision_path=route_decision_path,
        initial_labels=args.initial_label,
        loss_rebalance_labels=args.loss_rebalance_label,
    )
    outputs = write_model_capability_required_term_pair_fixed_retention_batch_closeout_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_fixed_retention_batch_closeout_text(report), end="")
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
