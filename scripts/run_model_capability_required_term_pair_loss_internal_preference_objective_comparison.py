from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_loss_internal_preference_objective_comparison import (  # noqa: E402
    build_model_capability_required_term_pair_loss_internal_preference_objective_comparison,
    locate_loss_internal_preference_objective_refresh_report,
    read_loss_internal_preference_objective_refresh_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_internal_preference_objective_comparison_artifacts import (  # noqa: E402
    render_loss_internal_preference_objective_comparison_text,
    write_loss_internal_preference_objective_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare loss-internal-preference required-term pair objective reports.")
    parser.add_argument("refresh_report", type=Path, nargs="+", help="Refresh report JSON paths or directories.")
    parser.add_argument("--source-label", action="append", default=[])
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-loss-internal-preference-objective-comparison")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    sources = [locate_loss_internal_preference_objective_refresh_report(path) for path in args.refresh_report]
    report = build_model_capability_required_term_pair_loss_internal_preference_objective_comparison(
        [read_loss_internal_preference_objective_refresh_report(path) for path in sources],
        source_paths=sources,
        source_labels=args.source_label,
    )
    outputs = write_loss_internal_preference_objective_comparison_outputs(report, args.out_dir)
    print(render_loss_internal_preference_objective_comparison_text(report), end="")
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
