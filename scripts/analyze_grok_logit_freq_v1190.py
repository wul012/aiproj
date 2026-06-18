from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.grok_logit_freq_v1190 import build_report, write_grok_logit_freq_outputs  # noqa: E402
from minigpt.grok_predict_v1186 import DEFAULT_CHECKPOINT  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402
from minigpt.script_runtime import choose_device  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze output-logit Fourier alignment for the grokking checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "grok-logit-freq-v1190")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        if not args.force:
            raise SystemExit(f"Output directory already exists: {args.out_dir}")
        import shutil

        shutil.rmtree(args.out_dir)
    device = choose_device(args.device)
    report = build_report(checkpoint_path=args.checkpoint, device=device)
    outputs = write_grok_logit_freq_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.require_pass and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
