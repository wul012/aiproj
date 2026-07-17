"""v1286 Phase B: CPU-only verdict + artifacts from the Phase-A cache and the
read-only v1281 reference cache (zero retrain).

Example:
    python scripts/analyze_grok_lr_compression_v1286.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_lr_compression_v1286 import build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import write_readability_outputs  # noqa: E402

STEM = "grok_lr_compression_v1286"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1286 Phase B analyzer")
    parser.add_argument("--cache", type=Path,
                        default=ROOT / "output" / "grok-lr-compression-v1286" / "phase_a_cache.pt")
    parser.add_argument("--reference", type=Path,
                        default=ROOT / "f" / "1281" / "解释" / "grok_norm_vs_step_v1281" / "phase_a_cache.pt")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-lr-compression-v1286")
    args = parser.parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    reference = torch.load(args.reference, weights_only=False)
    info = decide(cache, reference)
    report = build_report(cache, reference, info)
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM,
                                        row_title="Cells", row_key="cells")
    print("\n".join(summarize(report)))
    print(f"outputs={outputs}")


if __name__ == "__main__":
    main()
