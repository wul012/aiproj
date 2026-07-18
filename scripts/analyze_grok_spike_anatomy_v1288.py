"""v1288 Phase B: CPU-only verdict + artifacts from the Phase-A cache and the
read-only committed v1287 cache (zero retrain).

Example:
    python scripts/analyze_grok_spike_anatomy_v1288.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_spike_anatomy_v1288 import (  # noqa: E402
    build_report,
    decide,
    plot_result,
    summarize,
)
from minigpt.readability_report_artifacts import write_readability_outputs  # noqa: E402

STEM = "grok_spike_anatomy_v1288"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1288 Phase B analyzer")
    parser.add_argument("--cache", type=Path,
                        default=ROOT / "output" / "grok-spike-anatomy-v1288" / "phase_a_cache.pt")
    parser.add_argument("--reference", type=Path,
                        default=ROOT / "f" / "1287" / "解释" / "grok_purification_v1287" / "phase_a_cache.pt")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-spike-anatomy-v1288")
    parser.add_argument("--figure", type=Path, default=None)
    args = parser.parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    reference = torch.load(args.reference, weights_only=False)
    info = decide(cache, reference)
    report = build_report(cache, reference, info)
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM,
                                        row_title="Cells", row_key="cells")
    print("\n".join(summarize(report)))
    print(f"outputs={outputs}")
    if args.figure:
        plot_result(cache, info, args.figure)
        print(f"figure={args.figure}")


if __name__ == "__main__":
    main()
