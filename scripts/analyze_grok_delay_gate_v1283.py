"""v1283 Phase B: CPU-only verdict + artifacts from the Phase-A cache (zero retrain).

Example:
    python scripts/analyze_grok_delay_gate_v1283.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_delay_gate_v1283 import build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import write_readability_outputs  # noqa: E402

STEM = "grok_delay_gate_v1283"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1283 Phase B analyzer")
    parser.add_argument("--cache", type=Path,
                        default=ROOT / "output" / "grok-delay-gate-v1283" / "phase_a_cache.pt")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-delay-gate-v1283")
    args = parser.parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    info = decide(cache)
    report = build_report(cache, info)
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM,
                                        row_title="Cells", row_key="cells")
    print("\n".join(summarize(report)))
    print(f"outputs={outputs}")


if __name__ == "__main__":
    main()
