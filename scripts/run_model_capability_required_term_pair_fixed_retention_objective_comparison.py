from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import (  # noqa: E402
    build_model_capability_required_term_pair_fixed_retention_objective_comparison,
    locate_fixed_retention_objective_refresh_report,
    read_fixed_retention_objective_refresh_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison_artifacts import (  # noqa: E402
    render_fixed_retention_objective_comparison_text,
    write_fixed_retention_objective_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare fixed-retention objective refresh reports.")
    parser.add_argument("reports", nargs="+", type=Path, help="Coexistence refresh JSON files or directories.")
    parser.add_argument("--labels", nargs="*", default=None, help="Optional labels matching input reports.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-fixed-retention-objective-comparison")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    sources = [locate_fixed_retention_objective_refresh_report(path) for path in args.reports]
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_fixed_retention_objective_comparison(
        [read_fixed_retention_objective_refresh_report(source) for source in sources],
        source_paths=sources,
        source_labels=args.labels,
    )
    outputs = write_fixed_retention_objective_comparison_outputs(report, args.out_dir)
    print(render_fixed_retention_objective_comparison_text(report), end="")
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
