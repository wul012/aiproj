from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_surface_variant_selector import (  # noqa: E402
    build_surface_variant_selector,
    locate_surface_variant_selector_plan_source,
    locate_surface_variant_selector_replay_source,
    read_json_report,
    render_text,
    resolve_exit_code,
    write_surface_variant_selector_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select a stable contextual surface variant for demos and follow-up checks.")
    parser.add_argument("variant_plan", type=Path)
    parser.add_argument("variant_replay", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-surface-variant-selector")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    plan_source = locate_surface_variant_selector_plan_source(args.variant_plan)
    replay_source = locate_surface_variant_selector_replay_source(args.variant_replay)
    report = build_surface_variant_selector(
        read_json_report(plan_source),
        read_json_report(replay_source),
        plan_source_path=plan_source,
        replay_source_path=replay_source,
    )
    outputs = write_surface_variant_selector_outputs(report, args.out_dir)
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
