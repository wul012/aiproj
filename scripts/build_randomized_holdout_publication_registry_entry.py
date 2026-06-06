from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_registry_entry import (  # noqa: E402
    build_randomized_holdout_publication_registry_entry,
    locate_randomized_holdout_publication_decision_index,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_entry_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_registry_entry_text,
    write_randomized_holdout_publication_registry_entry_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a randomized holdout publication registry entry.")
    parser.add_argument("--publication-decision-index", type=Path, required=True, help="Publication decision index JSON or output directory.")
    parser.add_argument("--entry-id", default="randomized-holdout-publication-v928")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "randomized-holdout-publication-registry-entry")
    parser.add_argument("--require-entry-ready", action="store_true")
    parser.add_argument("--require-bounded-publication", action="store_true")
    parser.add_argument("--require-promotion-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    index_path = locate_randomized_holdout_publication_decision_index(args.publication_decision_index)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_registry_entry(
        read_json_report(index_path),
        publication_decision_index_path=index_path,
        entry_id=args.entry_id,
    )
    outputs = write_randomized_holdout_publication_registry_entry_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_registry_entry_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_entry_ready=args.require_entry_ready,
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
