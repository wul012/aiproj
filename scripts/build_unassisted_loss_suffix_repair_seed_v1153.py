from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402
from minigpt.unassisted_loss_suffix_repair_seed_v1153 import (  # noqa: E402
    build_unassisted_loss_suffix_repair_seed_v1153,
    default_v1149_seed_corpus_path,
    default_v1152_diagnostic_path,
    locate_v1149_seed_corpus,
    locate_v1152_diagnostic,
    read_json_report,
    resolve_exit_code,
    write_unassisted_loss_suffix_repair_seed_v1153_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the v1153 loss-suffix repair seed from the v1152 partial-signal diagnostic.")
    parser.add_argument("--diagnostic", type=Path, default=default_v1152_diagnostic_path(ROOT), help="v1152 diagnostic JSON or output directory.")
    parser.add_argument("--seed-corpus", type=Path, default=default_v1149_seed_corpus_path(ROOT), help="v1149 seed corpus JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "unassisted-loss-suffix-repair-seed-v1153")
    parser.add_argument("--require-seed-ready", action="store_true")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    diagnostic_path = locate_v1152_diagnostic(args.diagnostic)
    seed_path = locate_v1149_seed_corpus(args.seed_corpus)
    prepare_output_dir(args.out_dir, force=args.force)
    diagnostic = read_json_report(diagnostic_path, description="v1152 partial signal diagnostic")
    seed_report = read_json_report(seed_path, description="v1149 seed corpus")
    report = build_unassisted_loss_suffix_repair_seed_v1153(
        diagnostic,
        seed_report,
        diagnostic_path=diagnostic_path,
        seed_path=seed_path,
    )
    outputs = write_unassisted_loss_suffix_repair_seed_v1153_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(report, require_seed_ready=args.require_seed_ready)
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
