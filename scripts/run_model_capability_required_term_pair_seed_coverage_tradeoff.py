from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_seed_coverage_tradeoff import (  # noqa: E402
    build_model_capability_required_term_pair_seed_coverage_tradeoff,
    locate_pair_colon_immediate_stability,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_coverage_tradeoff_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_seed_coverage_tradeoff_text,
    write_model_capability_required_term_pair_seed_coverage_tradeoff_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare seed coverage tradeoffs across colon-immediate stability reports.")
    parser.add_argument("stability_reports", type=Path, nargs="+", help="Colon-immediate stability JSON files or output directories.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-seed-coverage-tradeoff")
    parser.add_argument("--label", action="append", default=None, help="Optional config label. Repeat in source order.")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when source validation fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    sources = [locate_pair_colon_immediate_stability(path) for path in args.stability_reports]
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_seed_coverage_tradeoff(
        [read_json_report(source) for source in sources],
        out_dir=args.out_dir,
        source_paths=sources,
        labels=args.label,
    )
    outputs = write_model_capability_required_term_pair_seed_coverage_tradeoff_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_seed_coverage_tradeoff_text(report), end="")
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
