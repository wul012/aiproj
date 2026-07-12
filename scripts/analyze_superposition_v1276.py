"""v1276 Phase B: cache-only metrics, verdict, artifacts, and figure."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.superposition_v1276 import SuperConfig, analyze, build_report, decide, plot_result  # noqa: E402

STEM = "superposition_v1276"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze the v1276 cache without training.")
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, map_location="cpu", weights_only=False)
    cfg = SuperConfig()
    result = analyze(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    plot_result(result, info, args.figure)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    print(f"figure={args.figure}")
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
