from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_surface_route_decision import (  # noqa: E402
    build_surface_route_decision,
    locate_surface_route_decision_contrast_source,
    locate_surface_route_decision_selector_source,
    read_json_report,
    render_text,
    resolve_exit_code,
    write_surface_route_decision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decide whether to close contextual surface policy route or pursue minimal prompts.")
    parser.add_argument("baseline_contrast", type=Path)
    parser.add_argument("variant_selector", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-surface-route-decision")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    contrast_source = locate_surface_route_decision_contrast_source(args.baseline_contrast)
    selector_source = locate_surface_route_decision_selector_source(args.variant_selector)
    report = build_surface_route_decision(
        read_json_report(contrast_source),
        read_json_report(selector_source),
        contrast_source_path=contrast_source,
        selector_source_path=selector_source,
    )
    outputs = write_surface_route_decision_outputs(report, args.out_dir)
    print(render_text(report), end="")
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
