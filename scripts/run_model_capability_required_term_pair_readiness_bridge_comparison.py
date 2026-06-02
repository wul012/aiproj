from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_bridge_comparison import (  # noqa: E402
    build_bridge_comparison,
    locate_bridge_comparison_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_bridge_comparison_artifacts import (  # noqa: E402
    render_bridge_comparison_text,
    write_bridge_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare objective-structure and direct-prompt bridge pair-readiness training runs.")
    parser.add_argument("--objective", type=Path, required=True, help="Objective-structure training run JSON or output directory.")
    parser.add_argument("--bridge", type=Path, required=True, help="Direct-prompt bridge training run JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-bridge-comparison")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when comparison inputs fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    objective_source = locate_bridge_comparison_source(args.objective)
    bridge_source = locate_bridge_comparison_source(args.bridge)
    report = build_bridge_comparison(
        objective_training_report=read_json_report(objective_source),
        bridge_training_report=read_json_report(bridge_source),
        objective_path=objective_source,
        bridge_path=bridge_source,
    )
    outputs = write_bridge_comparison_outputs(report, args.out_dir)
    print(render_bridge_comparison_text(report), end="")
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
