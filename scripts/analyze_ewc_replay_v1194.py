"""v1194 Phase B: CPU-only analysis over the cached EWC/replay frontiers (no training).

Loads the Phase-A cache, computes the best-min stability-plasticity scalar M for each method,
runs decide() (symmetric dominance + fairness gates), and writes the 5-format artifacts.

Example:
    python scripts/analyze_ewc_replay_v1194.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.continual_v1193 import ContinualConfig                              # noqa: E402
from minigpt.ewc_replay_v1194 import EWCReplayConfig, build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "ewc_replay_v1194"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1194 Phase B: EWC vs replay analysis over the cache.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "ewc-replay-v1194" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "ewc-replay-v1194")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    cfg = EWCReplayConfig(base=ContinualConfig(p=cache["config"]["p"]))
    print(f"loaded {args.cache}  (p={cache['config']['p']}, seeds={cache['config']['seeds']})")

    result = summarize(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print(f"\nM_replay={result['M_replay'][0]:.3f}±{result['M_replay'][1]:.3f}  "
          f"M_ewc={result['M_ewc'][0]:.3f}±{result['M_ewc'][1]:.3f}  "
          f"(EWC max accA={result['ewc_max_accA'][0]:.3f}, max accB={result['ewc_max_accB'][0]:.3f})")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
