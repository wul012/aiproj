from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.decoder_anchor_holdout_comparison_v1147 import (  # noqa: E402
    EXPLAIN_DIR_NAME,
    build_decoder_anchor_holdout_comparison_v1147,
    locate_v1146_report,
    read_json_report,
    resolve_comparison_paths,
    resolve_exit_code,
    write_decoder_anchor_holdout_comparison_v1147_outputs,
)
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402

DEFAULT_V1146_REPORT = (
    ROOT
    / "f"
    / "1146"
    / EXPLAIN_DIR_NAME
    / "model-capability-decoder-anchor-probe-v1146"
    / "model_capability_decoder_anchor_probe_v1146.json"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare v1146 decoder-anchor probe evidence with unassisted holdout replay.")
    parser.add_argument("--decoder-anchor-probe", type=Path, default=DEFAULT_V1146_REPORT, help="v1146 decoder-anchor probe JSON or output directory.")
    parser.add_argument("--loss-signal-distribution", type=Path, default=None, help="Optional v1145 loss-signal report for checkpoint fallback.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "decoder-anchor-holdout-comparison-v1147")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Override checkpoint path.")
    parser.add_argument("--tokenizer", type=Path, default=None, help="Override tokenizer path.")
    parser.add_argument("--device", choices=["cpu", "auto", "cuda"], default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return 1 if the comparison report does not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source_path = locate_v1146_report(args.decoder_anchor_probe)
    source = read_json_report(source_path, description="v1146 decoder anchor probe")
    paths = resolve_comparison_paths(
        source,
        decoder_probe_path=source_path,
        loss_signal_report_path=args.loss_signal_distribution,
        checkpoint_override=args.checkpoint,
        tokenizer_override=args.tokenizer,
    )
    report = build_decoder_anchor_holdout_comparison_v1147(
        source,
        checkpoint_path=paths["checkpoint"],
        tokenizer_path=paths["tokenizer"],
        device=args.device,
        decoder_probe_path=source_path,
        path_resolution=paths,
    )
    outputs = write_decoder_anchor_holdout_comparison_v1147_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
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
