from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_surface_branch_closeout import (  # noqa: E402
    SOURCE_FILENAMES,
    build_surface_branch_closeout,
    locate_closeout_source,
    read_json_report,
    render_text,
    resolve_exit_code,
    write_surface_branch_closeout_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close the required-term pair surface policy branch.")
    for source_id in SOURCE_FILENAMES:
        parser.add_argument(f"--{source_id.replace('_', '-')}", dest=source_id, type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-surface-branch-closeout")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source_paths = {source_id: locate_closeout_source(getattr(args, source_id), source_id) for source_id in SOURCE_FILENAMES}
    reports = {source_id: read_json_report(path) for source_id, path in source_paths.items()}
    report = build_surface_branch_closeout(reports, source_paths=source_paths)
    outputs = write_surface_branch_closeout_outputs(report, args.out_dir)
    print(render_text(report), end="")
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
