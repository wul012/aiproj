from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_decoder_anchor_probe_v1146 import (  # noqa: E402
    build_decoder_anchor_probe_v1146,
    read_json_report,
    resolve_exit_code,
    resolve_v1145_checkpoint_paths,
    write_decoder_anchor_probe_v1146_outputs,
)
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402

DEFAULT_V1145_REPORT = (
    ROOT
    / "f"
    / "1145"
    / "解释"
    / "model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145"
    / "model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.json"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1146 decoder-anchor local fragment probe against the v1145 checkpoint.")
    parser.add_argument("--loss-signal-distribution", type=Path, default=DEFAULT_V1145_REPORT, help="v1145 loss-signal/distribution JSON report.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "model-capability-decoder-anchor-probe-v1146")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Override checkpoint path.")
    parser.add_argument("--tokenizer", type=Path, default=None, help="Override tokenizer path.")
    parser.add_argument("--device", choices=["cpu", "auto", "cuda"], default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return 1 if the probe report does not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source = read_json_report(args.loss_signal_distribution, description="v1145 loss signal bridge decoder anchor distribution")
    paths = resolve_v1145_checkpoint_paths(
        source,
        report_path=args.loss_signal_distribution,
        checkpoint_override=args.checkpoint,
        tokenizer_override=args.tokenizer,
    )
    report = build_decoder_anchor_probe_v1146(
        source,
        checkpoint_path=paths["checkpoint"],
        tokenizer_path=paths["tokenizer"],
        device=args.device,
        source_report_path=args.loss_signal_distribution,
        path_resolution=paths,
    )
    outputs = write_decoder_anchor_probe_v1146_outputs(report, args.out_dir)
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
