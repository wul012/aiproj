from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt import (  # noqa: E402
    build_model_capability_route_promotion_release_readiness_downstream_receipt,
    locate_route_promotion_release_readiness_summary_check,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_readiness_downstream_receipt_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_release_readiness_downstream_receipt_text,
    write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a downstream receipt for a checked route-promotion release readiness summary.")
    parser.add_argument("--release-readiness-summary-check", type=Path, required=True, help="Release readiness summary check JSON or output directory.")
    parser.add_argument("--consumer-name", required=True)
    parser.add_argument("--route-id", required=True)
    parser.add_argument("--requested-scope", default="bounded_route_promotion_release_governance_only")
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-release-readiness-downstream-receipt")
    parser.add_argument("--require-receipt-ready", action="store_true", help="Return exit code 1 when the downstream receipt is blocked.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    check_path = locate_route_promotion_release_readiness_summary_check(args.release_readiness_summary_check)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_release_readiness_downstream_receipt(
        read_json_report(check_path),
        consumer_name=args.consumer_name,
        route_id=args.route_id,
        requested_scope=args.requested_scope,
        required_boundary=args.required_boundary,
        release_readiness_summary_check_path=check_path,
    )
    outputs = write_model_capability_route_promotion_release_readiness_downstream_receipt_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_release_readiness_downstream_receipt_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_receipt_ready=args.require_receipt_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
