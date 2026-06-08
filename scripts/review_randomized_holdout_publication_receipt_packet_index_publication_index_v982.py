from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_receipt_packet_index_publication_index_review_v982 import (  # noqa: E402
    build_randomized_holdout_publication_receipt_packet_index_publication_index_review_v982,
    locate_publication_index_v982,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_index_review_v982_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_receipt_packet_index_publication_index_review_v982_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_index_review_v982_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a randomized holdout publication receipt packet index publication index v982.")
    parser.add_argument("publication_index", type=Path, help="Publication index JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory for publication index review outputs.")
    parser.add_argument("--require-review-ready", action="store_true")
    parser.add_argument("--require-receipt-ready", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    index_path = locate_publication_index_v982(args.publication_index)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_receipt_packet_index_publication_index_review_v982(
        read_json_report(index_path),
        publication_index_path=index_path,
    )
    outputs = write_randomized_holdout_publication_receipt_packet_index_publication_index_review_v982_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_receipt_packet_index_publication_index_review_v982_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_review_ready=args.require_review_ready,
        require_receipt_ready=args.require_receipt_ready,
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
