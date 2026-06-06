from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.randomized_holdout_publication_registry_entry_check import (  # noqa: E402
    build_randomized_holdout_publication_registry_entry_check,
    locate_randomized_holdout_publication_registry_entry,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_entry_check_artifacts import (  # noqa: E402
    render_randomized_holdout_publication_registry_entry_check_text,
    write_randomized_holdout_publication_registry_entry_check_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a randomized holdout publication registry entry contract.")
    parser.add_argument("registry_entry", type=Path, help="Registry entry JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "randomized-holdout-publication-registry-entry-check")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    entry_path = locate_randomized_holdout_publication_registry_entry(args.registry_entry)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_randomized_holdout_publication_registry_entry_check(read_json_report(entry_path), registry_entry_path=entry_path)
    outputs = write_randomized_holdout_publication_registry_entry_check_outputs(report, args.out_dir)
    print(render_randomized_holdout_publication_registry_entry_check_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
