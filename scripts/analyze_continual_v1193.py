"""v1193 Phase B: CPU-only analysis over the cached continual-learning results (no training).

Loads the Phase-A cache, computes forgetting/replay/savings aggregates, runs decide(), and
writes the 5-format readability artifacts. Re-derivable with zero retrain (reuse-cached).

Example:
    python scripts/analyze_continual_v1193.py
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

from minigpt.continual_v1193 import ContinualConfig, build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "continual_v1193"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1193 Phase B: continual-learning analysis over the cache.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "continual-v1193" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "continual-v1193")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    cfg = ContinualConfig(p=cache["config"]["p"], task_a=cache["config"]["task_a"],
                          task_b=cache["config"]["task_b"])
    print(f"loaded {args.cache}  (A={cfg.task_a} B={cfg.task_b} p={cfg.p}, seeds={cache['config']['seeds']})")

    result = summarize(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print(f"\nA plateau {result['accA_plateau'][0]:.3f} -> after B {result['naive_accA_after_B'][0]:.3f} "
          f"(chance {result['chance']:.3f}) | forgetting {result['naive_forget'][0]:.3f} | "
          f"continue-on-A {result['continue_on_A_forget'][0]:.3f} | random-label-B {result['random_label_B_forget'][0]:.3f}")
    print("replay forgetting: " + ", ".join(f"buf{bs}={result['replay_forget'][bs][0]:.3f}" for bs in sorted(result['replay_forget'])))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
