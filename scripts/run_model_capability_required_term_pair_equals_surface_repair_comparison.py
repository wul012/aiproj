from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison import (  # noqa: E402
    build_model_capability_required_term_pair_equals_surface_repair_comparison,
    locate_pair_equals_surface_repair_report,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_equals_surface_repair_comparison_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_equals_surface_repair_comparison_text,
    write_model_capability_required_term_pair_equals_surface_repair_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare equals-surface repair reports for fixed/loss branch competition.")
    parser.add_argument("repair_reports", type=Path, nargs="+", help="Stability JSON files or output directories to compare.")
    parser.add_argument("--labels", nargs="*", default=None, help="Optional labels matching the input report order.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-equals-surface-repair-comparison")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when comparison inputs are invalid.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.labels is not None and len(args.labels) not in {0, len(args.repair_reports)}:
        raise SystemExit("--labels must be omitted or match the number of repair reports")
    sources = [locate_pair_equals_surface_repair_report(path) for path in args.repair_reports]
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_equals_surface_repair_comparison(
        [read_json_report(path) for path in sources],
        source_paths=sources,
        source_labels=args.labels,
    )
    outputs = write_model_capability_required_term_pair_equals_surface_repair_comparison_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_equals_surface_repair_comparison_text(report), end="")
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
