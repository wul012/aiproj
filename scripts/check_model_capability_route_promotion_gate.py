from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_gate import (  # noqa: E402
    build_model_capability_route_promotion_gate,
    locate_route_promotion_portfolio,
    locate_route_promotion_regression_monitor,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_gate_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_gate_text,
    write_model_capability_route_promotion_gate_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the route-promotion portfolio gate.")
    parser.add_argument("--portfolio", type=Path, required=True, help="Route promotion portfolio JSON or output directory.")
    parser.add_argument("--regression-monitor", type=Path, required=True, help="Route promotion regression monitor JSON or output directory.")
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-gate")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when gate checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    portfolio_path = locate_route_promotion_portfolio(args.portfolio)
    monitor_path = locate_route_promotion_regression_monitor(args.regression_monitor)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_gate(
        read_json_report(portfolio_path),
        read_json_report(monitor_path),
        portfolio_path=portfolio_path,
        regression_monitor_path=monitor_path,
        required_boundary=args.required_boundary,
    )
    outputs = write_model_capability_route_promotion_gate_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_gate_text(report), end="")
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
