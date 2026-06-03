from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_history import (  # noqa: E402
    build_model_capability_route_promotion_history,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_history_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_history_text,
    write_model_capability_route_promotion_history_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a model capability route-promotion history ledger.")
    parser.add_argument("manifests", nargs="+", type=Path, help="Route promotion manifest JSON files or output directories.")
    parser.add_argument("--names", nargs="*", default=None, help="Optional names matching manifests.")
    parser.add_argument("--min-ready-entries", type=int, default=1)
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--require-ready-history", action="store_true", help="Return exit code 1 when route history readiness fails.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-route-promotion-history",
    )
    parser.add_argument("--title", default="MiniGPT model capability route promotion history")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_history(
        args.manifests,
        names=args.names,
        min_ready_entries=args.min_ready_entries,
        required_boundary=args.required_boundary,
        title=args.title,
    )
    outputs = write_model_capability_route_promotion_history_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_history_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_ready_history=args.require_ready_history):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
