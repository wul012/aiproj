from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_downstream_guard import (  # noqa: E402
    build_model_capability_route_promotion_downstream_guard,
    locate_route_promotion_governance_snapshot,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_downstream_guard_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_downstream_guard_text,
    write_model_capability_route_promotion_downstream_guard_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check downstream access to a bounded route-promotion card.")
    parser.add_argument("--governance-snapshot", type=Path, required=True, help="Governance snapshot JSON or output directory.")
    parser.add_argument("--route-id", required=True)
    parser.add_argument("--consumer-name", required=True)
    parser.add_argument("--requested-scope", default="bounded_model_capability_governance_only")
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-downstream-guard")
    parser.add_argument("--require-allowed", action="store_true", help="Return exit code 1 when access is not allowed.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    snapshot_path = locate_route_promotion_governance_snapshot(args.governance_snapshot)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_downstream_guard(
        read_json_report(snapshot_path),
        route_id=args.route_id,
        consumer_name=args.consumer_name,
        requested_scope=args.requested_scope,
        required_boundary=args.required_boundary,
        governance_snapshot_path=snapshot_path,
    )
    outputs = write_model_capability_route_promotion_downstream_guard_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_downstream_guard_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_allowed=args.require_allowed):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
