from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision,
    locate_decoder_anchor_distribution_audit,
    locate_decoder_anchor_seed_revision,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a rebalanced decoder-anchor seed revision after distribution audit.")
    parser.add_argument("--decoder-anchor-seed", type=Path, required=True, help="Decoder-anchor seed revision JSON or output directory.")
    parser.add_argument("--distribution-audit", type=Path, required=True, help="Decoder-anchor distribution audit JSON or output directory.")
    parser.add_argument("--carry-forward-per-case", type=int, default=2, help="Maximum carry-forward rows to keep per case.")
    parser.add_argument("--direct-rebalance-copies-per-case", type=int, default=2, help="Direct-answer weighting rows to add per case.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-seed-revision")
    parser.add_argument("--require-seed-ready", action="store_true", help="Return exit code 1 when the rebalanced seed is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_path = locate_decoder_anchor_seed_revision(args.decoder_anchor_seed)
    audit_path = locate_decoder_anchor_distribution_audit(args.distribution_audit)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision(
        read_json_report(seed_path),
        read_json_report(audit_path),
        seed_revision_path=seed_path,
        distribution_audit_path=audit_path,
        carry_forward_per_case=args.carry_forward_per_case,
        direct_rebalance_copies_per_case=args.direct_rebalance_copies_per_case,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_seed_ready=args.require_seed_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
