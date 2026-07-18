"""v1287 Phase B: CPU-only verdict + artifacts from the Phase-A cache and the
two read-only committed reference caches (zero retrain).

Example:
    python scripts/analyze_grok_purification_v1287.py --figure out.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_purification_v1287 import (  # noqa: E402
    build_report,
    decide,
    plot_result,
    summarize,
)
from minigpt.readability_report_artifacts import write_readability_outputs  # noqa: E402

STEM = "grok_purification_v1287"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1287 Phase B analyzer")
    parser.add_argument("--cache", type=Path,
                        default=ROOT / "output" / "grok-purification-v1287" / "phase_a_cache.pt")
    parser.add_argument("--ref-canonical", type=Path,
                        default=ROOT / "f" / "1285" / "解释" / "grok_deep_plateau_v1285" / "phase_a_cache.pt")
    parser.add_argument("--ref-compressed", type=Path,
                        default=ROOT / "f" / "1286" / "解释" / "grok_lr_compression_v1286" / "phase_a_cache.pt")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-purification-v1287")
    parser.add_argument("--figure", type=Path, default=None)
    args = parser.parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    ref_canonical = torch.load(args.ref_canonical, weights_only=False)
    ref_compressed = torch.load(args.ref_compressed, weights_only=False)
    info = decide(cache, ref_canonical, ref_compressed)
    report = build_report(cache, ref_canonical, ref_compressed, info)
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM,
                                        row_title="Cells", row_key="cells")
    print("\n".join(summarize(report)))
    print(f"outputs={outputs}")
    if args.figure:
        plot_result(cache, ref_canonical, ref_compressed, info, args.figure)
        print(f"figure={args.figure}")


if __name__ == "__main__":
    main()
