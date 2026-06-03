from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_portfolio import (  # noqa: E402
    build_model_capability_route_promotion_portfolio,
    locate_route_promotion_history,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_portfolio_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_portfolio_text,
    write_model_capability_route_promotion_portfolio_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a model capability route-promotion portfolio snapshot.")
    parser.add_argument("--history", type=Path, required=True, help="Route promotion history JSON file or output directory.")
    parser.add_argument("--min-ready-routes", type=int, default=1)
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--require-ready-portfolio", action="store_true", help="Return exit code 1 when portfolio checks fail.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-route-promotion-portfolio",
    )
    parser.add_argument("--title", default="MiniGPT model capability route promotion portfolio")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    history_path = locate_route_promotion_history(args.history)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_portfolio(
        read_json_report(history_path),
        source_history_path=history_path,
        min_ready_routes=args.min_ready_routes,
        required_boundary=args.required_boundary,
        title=args.title,
    )
    outputs = write_model_capability_route_promotion_portfolio_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_portfolio_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_ready_portfolio=args.require_ready_portfolio):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
