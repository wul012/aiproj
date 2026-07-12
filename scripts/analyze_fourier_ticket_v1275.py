"""v1275 Phase B: CPU-only verdict and artifacts from the frozen cache."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.fourier_ticket_v1275 import TicketConfig, build_report, decide, plot_result  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "fourier_ticket_v1275"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze the v1275 cache without retraining.")
    parser.add_argument("--cache", type=Path, default=ROOT / "output" / "fourier-ticket-v1275" / "cache.pt")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "fourier-ticket-v1275")
    parser.add_argument("--figure", type=Path, default=ROOT / "output" / "fourier-ticket-v1275" / "fourier-ticket-v1275.png")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, map_location="cpu", weights_only=False)
    cfg = TicketConfig()
    info = decide(cache, cfg)
    report = build_report(cache, info)
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    plot_result(cache, args.figure)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    print(f"figure={args.figure}")
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
