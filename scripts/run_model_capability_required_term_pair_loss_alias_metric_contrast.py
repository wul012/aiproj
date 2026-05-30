from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_loss_alias_metric_contrast import (  # noqa: E402
    build_model_capability_required_term_pair_loss_alias_metric_contrast,
    locate_loss_alias_metric_contrast_focus_source,
    locate_loss_alias_metric_contrast_stability_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_metric_contrast_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_loss_alias_metric_contrast_text,
    write_model_capability_required_term_pair_loss_alias_metric_contrast_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare source stability and focused loss-alias metrics.")
    parser.add_argument("stability", type=Path, help="v519 stability metrics JSON or output directory.")
    parser.add_argument("focus", type=Path, help="v518 focus metrics JSON or output directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-loss-alias-metric-contrast",
    )
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when source reports fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    stability_source = locate_loss_alias_metric_contrast_stability_source(args.stability)
    focus_source = locate_loss_alias_metric_contrast_focus_source(args.focus)
    report = build_model_capability_required_term_pair_loss_alias_metric_contrast(
        read_json_report(stability_source),
        read_json_report(focus_source),
        out_dir=args.out_dir,
        stability_source_path=stability_source,
        focus_source_path=focus_source,
    )
    outputs = write_model_capability_required_term_pair_loss_alias_metric_contrast_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_loss_alias_metric_contrast_text(report), end="")
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
