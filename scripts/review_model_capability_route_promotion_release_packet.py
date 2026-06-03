from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_release_packet_review import (  # noqa: E402
    build_model_capability_route_promotion_release_packet_review,
    locate_route_promotion_release_packet,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_packet_review_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_release_packet_review_text,
    write_model_capability_route_promotion_release_packet_review_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a route-promotion release packet.")
    parser.add_argument("--release-packet", type=Path, required=True, help="Release packet JSON or output directory.")
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-release-packet-review")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when review checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    packet_path = locate_route_promotion_release_packet(args.release_packet)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_release_packet_review(
        read_json_report(packet_path),
        release_packet_path=packet_path,
        required_boundary=args.required_boundary,
    )
    outputs = write_model_capability_route_promotion_release_packet_review_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_release_packet_review_text(report), end="")
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
