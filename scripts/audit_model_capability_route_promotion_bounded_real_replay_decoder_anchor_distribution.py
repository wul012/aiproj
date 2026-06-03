from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit,
    locate_decoder_anchor_failure_diagnostic,
    locate_decoder_anchor_seed_revision,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit decoder-anchor seed distribution before further training.")
    parser.add_argument("--decoder-anchor-seed", type=Path, required=True, help="Decoder-anchor seed revision JSON or output directory.")
    parser.add_argument("--failure-diagnostic", type=Path, required=True, help="Decoder-anchor failure diagnostic JSON or output directory.")
    parser.add_argument("--corpus", type=Path, required=True, help="Decoder-anchor corpus text file.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-decoder-anchor-distribution-audit")
    parser.add_argument("--require-audit-ready", action="store_true", help="Return exit code 1 when audit inputs are not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_path = locate_decoder_anchor_seed_revision(args.decoder_anchor_seed)
    diagnostic_path = locate_decoder_anchor_failure_diagnostic(args.failure_diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit(
        read_json_report(seed_path),
        read_json_report(diagnostic_path),
        corpus_path=args.corpus,
        seed_revision_path=seed_path,
        diagnostic_path=diagnostic_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_audit_ready=args.require_audit_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
