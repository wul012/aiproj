from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_registry_packet import (  # noqa: E402
    build_randomized_holdout_publication_registry_packet,
    locate_randomized_holdout_publication_registry_entry,
    locate_randomized_holdout_publication_registry_entry_check,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_packet_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_registry_packet_text,
    write_randomized_holdout_publication_registry_packet_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a randomized holdout publication registry packet.")
    parser.add_argument("--registry-entry", type=Path, required=True, help="Registry entry JSON or output directory.")
    parser.add_argument("--registry-entry-check", type=Path, required=True, help="Registry entry contract check JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "randomized-holdout-publication-registry-packet")
    parser.add_argument("--require-packet-ready", action="store_true")
    parser.add_argument("--require-bounded-publication", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    entry_path = locate_randomized_holdout_publication_registry_entry(args.registry_entry)
    check_path = locate_randomized_holdout_publication_registry_entry_check(args.registry_entry_check)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_registry_packet(
        read_json_report(entry_path),
        read_json_report(check_path),
        registry_entry_path=entry_path,
        registry_entry_check_path=check_path,
    )
    outputs = write_randomized_holdout_publication_registry_packet_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_registry_packet_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_packet_ready=args.require_packet_ready,
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
