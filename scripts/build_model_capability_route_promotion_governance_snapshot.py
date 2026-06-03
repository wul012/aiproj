from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_governance_snapshot import (  # noqa: E402
    build_model_capability_route_promotion_governance_snapshot,
    locate_route_promotion_decision_index,
    locate_route_promotion_decision_index_check,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_governance_snapshot_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_governance_snapshot_text,
    write_model_capability_route_promotion_governance_snapshot_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bounded route-promotion governance snapshot.")
    parser.add_argument("--decision-index", type=Path, required=True, help="Decision index JSON or output directory.")
    parser.add_argument("--index-check", type=Path, required=True, help="Decision index contract check JSON or output directory.")
    parser.add_argument("--required-boundary", default="tiny_required_term_pair_probe_only")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-governance-snapshot")
    parser.add_argument("--require-ready-snapshot", action="store_true", help="Return exit code 1 when the snapshot is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    index_path = locate_route_promotion_decision_index(args.decision_index)
    check_path = locate_route_promotion_decision_index_check(args.index_check)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_governance_snapshot(
        read_json_report(index_path),
        read_json_report(check_path),
        decision_index_path=index_path,
        index_contract_check_path=check_path,
        required_boundary=args.required_boundary,
    )
    outputs = write_model_capability_route_promotion_governance_snapshot_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_governance_snapshot_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_ready_snapshot=args.require_ready_snapshot):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
