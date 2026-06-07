from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt import (  # noqa: E402
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a downstream consumer receipt for a randomized holdout publication receipt packet index publication index review.")
    parser.add_argument("--index-review", type=Path, required=True, help="Publication index review JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory for receipt outputs.")
    parser.add_argument("--consumer-name", default="publication_registry_governance_lookup_reader")
    parser.add_argument("--requested-use", default="downstream_governance_lookup_only")
    parser.add_argument("--require-receipt-ready", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    review_path = locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review(args.index_review)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt(
        read_json_report(review_path),
        index_review_path=review_path,
        consumer_name=args.consumer_name,
        requested_use=args.requested_use,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_receipt_ready=args.require_receipt_ready, require_promotion_ready=args.require_promotion_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
