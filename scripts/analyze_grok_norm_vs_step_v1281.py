"""v1281 Phase B: CPU-only verdict + artifacts from the Phase-A cache and the
read-only v1279/v1280 reference caches (zero retrain).

Example:
    python scripts/analyze_grok_norm_vs_step_v1281.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_norm_vs_step_v1281 import build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import write_readability_outputs  # noqa: E402

STEM = "grok_norm_vs_step_v1281"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1281 Phase B analyzer")
    parser.add_argument("--cache", type=Path,
                        default=ROOT / "output" / "grok-norm-vs-step-v1281" / "phase_a_cache.pt")
    parser.add_argument("--ref80", type=Path,
                        default=ROOT / "f" / "1280" / "解释" / "grok_init_rescue_v1280" / "phase_a_cache.pt")
    parser.add_argument("--ref79", type=Path,
                        default=ROOT / "f" / "1279" / "解释" / "grok_speed_v1279" / "phase_a_cache.pt")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-norm-vs-step-v1281")
    args = parser.parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    ref80 = torch.load(args.ref80, weights_only=False)
    ref79 = torch.load(args.ref79, weights_only=False)
    info = decide(cache, ref80, ref79)
    report = build_report(cache, ref80, ref79, info)
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM,
                                        row_title="Cells", row_key="cells")
    print("\n".join(summarize(report)))
    print(f"outputs={outputs}")


if __name__ == "__main__":
    main()
