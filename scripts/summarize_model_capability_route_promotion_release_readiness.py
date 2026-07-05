from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_release_readiness_summary import (  # noqa: E402
    build_model_capability_route_promotion_release_readiness_summary,
    locate_route_promotion_governance_snapshot,
    locate_route_promotion_release_packet,
    locate_route_promotion_release_packet_review,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_readiness_summary_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_release_readiness_summary_text,
    write_model_capability_route_promotion_release_readiness_summary_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize bounded route-promotion release readiness evidence.")
    parser.add_argument("--release-packet", type=Path, required=True, help="Release packet JSON or output directory.")
    parser.add_argument("--release-packet-review", type=Path, required=True, help="Release packet review JSON or output directory.")
    parser.add_argument("--governance-snapshot", type=Path, required=True, help="Governance snapshot JSON or output directory.")
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-release-readiness-summary")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when release readiness checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    release_packet_path = locate_route_promotion_release_packet(args.release_packet)
    release_packet_review_path = locate_route_promotion_release_packet_review(args.release_packet_review)
    governance_snapshot_path = locate_route_promotion_governance_snapshot(args.governance_snapshot)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_release_readiness_summary(
        read_json_report(release_packet_path),
        read_json_report(release_packet_review_path),
        read_json_report(governance_snapshot_path),
        release_packet_path=release_packet_path,
        release_packet_review_path=release_packet_review_path,
        governance_snapshot_path=governance_snapshot_path,
        required_boundary=args.required_boundary,
    )
    outputs = write_model_capability_route_promotion_release_readiness_summary_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_release_readiness_summary_text(report), end="")
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
