from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_decision_index import (  # noqa: E402
    build_randomized_holdout_publication_decision_index,
    locate_randomized_holdout_acceptance_publication_packet,
    locate_randomized_holdout_publication_decision,
    locate_randomized_holdout_publication_packet_review,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_decision_index_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_decision_index_text,
    write_randomized_holdout_publication_decision_index_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a randomized holdout publication decision index.")
    parser.add_argument("--publication-decision", type=Path, required=True, help="Publication decision JSON or output directory.")
    parser.add_argument("--publication-review", type=Path, required=True, help="Publication packet review JSON or output directory.")
    parser.add_argument("--publication-packet", type=Path, required=True, help="Acceptance publication packet JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "randomized-holdout-publication-decision-index")
    parser.add_argument("--require-index-ready", action="store_true")
    parser.add_argument("--require-bounded-publication", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    decision_path = locate_randomized_holdout_publication_decision(args.publication_decision)
    review_path = locate_randomized_holdout_publication_packet_review(args.publication_review)
    packet_path = locate_randomized_holdout_acceptance_publication_packet(args.publication_packet)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_decision_index(
        read_json_report(decision_path),
        read_json_report(review_path),
        read_json_report(packet_path),
        publication_decision_path=decision_path,
        publication_review_path=review_path,
        publication_packet_path=packet_path,
    )
    outputs = write_randomized_holdout_publication_decision_index_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_decision_index_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_index_ready=args.require_index_ready,
        require_bounded_publication=args.require_bounded_publication,
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
