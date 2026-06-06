from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_bounded_promotion_decision import (  # noqa: E402
    build_randomized_holdout_bounded_promotion_decision,
    locate_randomized_holdout_bounded_promotion_gate,
    locate_randomized_holdout_candidate_packet,
    locate_randomized_holdout_candidate_packet_review,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_bounded_promotion_decision_artifacts import (  # noqa: E402
    render_randomized_holdout_bounded_promotion_decision_text,
    write_randomized_holdout_bounded_promotion_decision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a bounded randomized holdout promotion decision.")
    parser.add_argument("--gate", type=Path, required=True, help="Bounded gate JSON or output directory.")
    parser.add_argument("--candidate-packet-review", type=Path, required=True, help="Candidate packet review JSON or output directory.")
    parser.add_argument("--candidate-packet", type=Path, required=True, help="Candidate packet JSON or output directory.")
    parser.add_argument("--minimum-candidate-cases", type=int, default=20)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "randomized-holdout-bounded-promotion-decision")
    parser.add_argument("--require-decision-ready", action="store_true")
    parser.add_argument("--require-bounded-acceptance", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    gate_path = locate_randomized_holdout_bounded_promotion_gate(args.gate)
    review_path = locate_randomized_holdout_candidate_packet_review(args.candidate_packet_review)
    packet_path = locate_randomized_holdout_candidate_packet(args.candidate_packet)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_bounded_promotion_decision(
        read_json_report(gate_path),
        read_json_report(review_path),
        read_json_report(packet_path),
        gate_path=gate_path,
        candidate_packet_review_path=review_path,
        candidate_packet_path=packet_path,
        minimum_candidate_cases=args.minimum_candidate_cases,
    )
    outputs = write_randomized_holdout_bounded_promotion_decision_outputs(report, args.out_dir)
    print(render_randomized_holdout_bounded_promotion_decision_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_decision_ready=args.require_decision_ready,
        require_bounded_acceptance=args.require_bounded_acceptance,
        require_promotion_ready=args.require_promotion_ready,
    )
    if code:
        raise SystemExit(code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
