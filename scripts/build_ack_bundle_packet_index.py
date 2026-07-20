from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.ack_bundle_packet_index import (  # noqa: E402
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check,
    read_json_report,
    resolve_exit_code,
)
from minigpt.ack_bundle_packet_index_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index.")
    parser.add_argument("--receipt-packet", type=Path, required=True, help="Receipt packet JSON or output directory.")
    parser.add_argument("--receipt-packet-check", type=Path, required=True, help="Receipt packet contract check JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory for receipt packet index outputs.")
    parser.add_argument("--require-index-ready", action="store_true")
    parser.add_argument("--require-lookup-ready", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    packet_path = locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet(args.receipt_packet)
    check_path = locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(args.receipt_packet_check)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index(
        read_json_report(packet_path),
        read_json_report(check_path),
        receipt_packet_path=packet_path,
        receipt_packet_check_path=check_path,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_index_ready=args.require_index_ready,
        require_lookup_ready=args.require_lookup_ready,
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
