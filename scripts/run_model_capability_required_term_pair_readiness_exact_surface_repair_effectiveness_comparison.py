from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison import (  # noqa: E402
    build_exact_surface_repair_effectiveness_comparison,
    locate_exact_surface_repair_effectiveness_replay_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison_artifacts import (  # noqa: E402
    render_exact_surface_repair_effectiveness_comparison_text,
    write_exact_surface_repair_effectiveness_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare exact-surface repair replay effectiveness against a baseline replay.")
    parser.add_argument("baseline_replay", type=Path, help="Baseline pair-probe replay JSON or output directory.")
    parser.add_argument("repaired_replay", type=Path, help="Repaired pair-probe replay JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-exact-surface-repair-effectiveness-comparison")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when comparison fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    baseline_source = locate_exact_surface_repair_effectiveness_replay_source(args.baseline_replay)
    repaired_source = locate_exact_surface_repair_effectiveness_replay_source(args.repaired_replay)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_exact_surface_repair_effectiveness_comparison(
        read_json_report(baseline_source),
        read_json_report(repaired_source),
        baseline_replay_path=baseline_source,
        repaired_replay_path=repaired_source,
    )
    outputs = write_exact_surface_repair_effectiveness_comparison_outputs(report, args.out_dir)
    print(render_exact_surface_repair_effectiveness_comparison_text(report), end="")
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
