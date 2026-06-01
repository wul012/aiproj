from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_generation_internal_alignment_route_decision import (  # noqa: E402
    build_model_capability_required_term_pair_generation_internal_alignment_route_decision,
    locate_generation_internal_alignment_route_decision_input,
    read_generation_internal_alignment_route_decision_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_internal_alignment_route_decision_artifacts import (  # noqa: E402
    render_generation_internal_alignment_route_decision_text,
    write_generation_internal_alignment_route_decision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decide the next route from a generation/internal alignment comparison.")
    parser.add_argument("comparison_report", type=Path, help="Alignment comparison JSON path or output directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-generation-internal-alignment-route-decision",
    )
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source = locate_generation_internal_alignment_route_decision_input(args.comparison_report)
    report = build_model_capability_required_term_pair_generation_internal_alignment_route_decision(
        read_generation_internal_alignment_route_decision_input(source)
    )
    outputs = write_generation_internal_alignment_route_decision_outputs(report, args.out_dir)
    print(render_generation_internal_alignment_route_decision_text(report), end="")
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
