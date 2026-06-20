"""v1196 Phase B: CPU-only analysis over the cached induction sweep (no training).

Loads the Phase-A cache, computes the W*-ordering depth verdict + controls, and writes the
5-format readability artifacts. Re-derivable with zero retrain (reuse-cached).

Example:
    python scripts/analyze_induction_v1196.py
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

from minigpt.induction_v1196 import InductionConfig, build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "induction_v1196"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1196 Phase B: induction depth analysis over the cache.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "induction-v1196" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "induction-v1196")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    cfg = InductionConfig(K=cache["config"]["K"], T=cache["config"]["T"],
                          widths=tuple(cache["config"]["widths"]), depths=tuple(cache["config"]["depths"]),
                          shortcut_widths=tuple(cache["config"]["shortcut_widths"]),
                          attn_only_widths=tuple(cache["config"]["attn_only_widths"]),
                          seeds=tuple(cache["config"]["seeds"]))
    print(f"loaded {args.cache}  (K={cfg.K} T={cfg.T} widths={cfg.widths} seeds={cache['config']['seeds']})")

    result = summarize(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print(f"\nS={result['S']:.3f}  unigram {result['unigram_acc']:.3f}  random-init {result['random_init_acc']:.3f}")
    for d in result["depths"]:
        line = "  ".join(f"w{w}:{result['cells'][(d, w)]['acc'][0]:.2f}" for w in result["widths"])
        print(f"depth{d} acc: {line}")
    print(f"W*_1L={info['flags']['wstar_1L']} W*_2L={info['flags']['wstar_2L']}  "
          f"shortcut 1L max={info['flags']['shortcut_1L_max_acc']}  "
          f"attn-only 2L max={info['flags']['attn_only_2L_max_acc']} / 1L max={info['flags']['attn_only_1L_max_acc']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
