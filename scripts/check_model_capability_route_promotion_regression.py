from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_regression_monitor import (  # noqa: E402
    build_model_capability_route_promotion_regression_monitor,
    locate_route_promotion_portfolio,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_regression_monitor_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_regression_monitor_text,
    write_model_capability_route_promotion_regression_monitor_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check route-promotion portfolio regressions against a baseline portfolio.")
    parser.add_argument("--current", type=Path, required=True, help="Current route promotion portfolio JSON or output directory.")
    parser.add_argument("--baseline", type=Path, default=None, help="Optional baseline portfolio JSON or output directory. Defaults to current.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-regression-monitor")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when regressions are detected.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    current_path = locate_route_promotion_portfolio(args.current)
    baseline_path = locate_route_promotion_portfolio(args.baseline) if args.baseline else current_path
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_regression_monitor(
        read_json_report(current_path),
        baseline_portfolio=read_json_report(baseline_path),
        current_path=current_path,
        baseline_path=baseline_path,
    )
    outputs = write_model_capability_route_promotion_regression_monitor_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_regression_monitor_text(report), end="")
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
