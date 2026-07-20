from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993 import (  # noqa: E402
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993,
    locate_publication_check_v993,
    locate_publication_v993,
    read_json_report,
    resolve_exit_code,
)
from minigpt.packet_chain_index_v993_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a randomized holdout publication receipt index publication index v993.")
    parser.add_argument("--publication", type=Path, required=True, help="Publication JSON or output directory.")
    parser.add_argument("--publication-check", type=Path, required=True, help="Publication contract check JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Directory for publication index outputs.")
    parser.add_argument("--require-index-ready", action="store_true")
    parser.add_argument("--require-lookup-ready", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    publication_path = locate_publication_v993(args.publication)
    check_path = locate_publication_check_v993(args.publication_check)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993(
        read_json_report(publication_path),
        read_json_report(check_path),
        publication_path=publication_path,
        publication_check_path=check_path,
    )
    outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(report, require_index_ready=args.require_index_ready, require_lookup_ready=args.require_lookup_ready, require_promotion_ready=args.require_promotion_ready)
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
