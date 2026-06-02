from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_repair_comparison import (  # noqa: E402
    build_pair_readiness_repair_comparison,
    locate_pair_readiness_repair_comparison_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_repair_comparison_artifacts import (  # noqa: E402
    render_pair_readiness_repair_comparison_text,
    write_pair_readiness_repair_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare baseline and loss-retention pair-readiness training runs.")
    parser.add_argument("--baseline", type=Path, required=True, help="Baseline pair-readiness training run JSON or output directory.")
    parser.add_argument("--candidate", type=Path, required=True, help="Candidate pair-readiness training run JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-repair-comparison")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when comparison inputs fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    baseline = locate_pair_readiness_repair_comparison_source(args.baseline)
    candidate = locate_pair_readiness_repair_comparison_source(args.candidate)
    report = build_pair_readiness_repair_comparison(
        baseline_report=read_json_report(baseline),
        candidate_report=read_json_report(candidate),
        baseline_path=baseline,
        candidate_path=candidate,
    )
    outputs = write_pair_readiness_repair_comparison_outputs(report, args.out_dir)
    print(render_pair_readiness_repair_comparison_text(report), end="")
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
