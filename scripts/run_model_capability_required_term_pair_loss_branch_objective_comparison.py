from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_loss_branch_objective_comparison import (  # noqa: E402
    build_model_capability_required_term_pair_loss_branch_objective_comparison,
    locate_loss_branch_objective_refresh_report,
    read_loss_branch_objective_refresh_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_branch_objective_comparison_artifacts import (  # noqa: E402
    render_loss_branch_objective_comparison_text,
    write_loss_branch_objective_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare loss-branch objective refresh reports.")
    parser.add_argument("refresh_reports", type=Path, nargs="+", help="Refresh JSON files or output directories.")
    parser.add_argument("--labels", nargs="*", default=None, help="Optional labels matching the input report order.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-loss-branch-objective-comparison")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when comparison inputs are invalid.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.labels is not None and len(args.labels) not in {0, len(args.refresh_reports)}:
        raise SystemExit("--labels must be omitted or match the number of refresh reports")
    sources = [locate_loss_branch_objective_refresh_report(path) for path in args.refresh_reports]
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_loss_branch_objective_comparison(
        [read_loss_branch_objective_refresh_report(path) for path in sources],
        source_paths=sources,
        source_labels=args.labels,
    )
    outputs = write_loss_branch_objective_comparison_outputs(report, args.out_dir)
    print(render_loss_branch_objective_comparison_text(report), end="")
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
