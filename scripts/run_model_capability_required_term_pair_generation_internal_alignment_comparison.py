from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison import (  # noqa: E402
    build_model_capability_required_term_pair_generation_internal_alignment_comparison,
    locate_generation_internal_alignment_forced_choice_report,
    locate_generation_internal_alignment_refresh_report,
    make_generation_internal_alignment_source,
    read_generation_internal_alignment_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_internal_alignment_comparison_artifacts import (  # noqa: E402
    render_generation_internal_alignment_comparison_text,
    write_generation_internal_alignment_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare required-term pair generation and internal alignment.")
    parser.add_argument(
        "--source",
        action="append",
        nargs=3,
        metavar=("LABEL", "REFRESH_REPORT", "FORCED_CHOICE_REPORT"),
        required=True,
        help="Route label, refresh report JSON/dir, and forced-choice diagnostic JSON/dir.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-generation-internal-alignment-comparison",
    )
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    sources = []
    for label, refresh_input, forced_input in args.source:
        refresh_path = locate_generation_internal_alignment_refresh_report(refresh_input)
        forced_path = locate_generation_internal_alignment_forced_choice_report(forced_input)
        sources.append(
            make_generation_internal_alignment_source(
                label=label,
                refresh_report=read_generation_internal_alignment_report(refresh_path),
                forced_choice_report=read_generation_internal_alignment_report(forced_path),
                refresh_path=refresh_path,
                forced_choice_path=forced_path,
            )
        )
    report = build_model_capability_required_term_pair_generation_internal_alignment_comparison(sources)
    outputs = write_generation_internal_alignment_comparison_outputs(report, args.out_dir)
    print(render_generation_internal_alignment_comparison_text(report), end="")
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
