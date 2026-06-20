"""v1196 Phase A: train the induction depth-vs-width sweep ONCE and save the cache.

Per (depth, width, seed): train on the CLEAN induction task (random sequence, most-recent-successor
target, first occurrences masked) and log inductable accuracy + the causal swap probe + mechanistic
attention scores. Plus a 1-layer fixed-offset shortcut-control (capability) and attention-only
(MLP-zeroed) arms. No verdict logic (Phase B re-derives from the cache with zero retrain).

Example:
    python scripts/run_induction_v1196.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.induction_v1196 import InductionConfig, run_phase_a  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1196 Phase A: induction depth-vs-width sweep, save cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "induction-v1196" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--seeds", type=int, default=5)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(1337)
    device = choose_device(args.device)
    cfg = InductionConfig(seeds=tuple(1337 + i for i in range(args.seeds)))
    print(f"device={device} K={cfg.K} T={cfg.T} widths={cfg.widths} depths={cfg.depths} "
          f"seeds={cfg.seeds} S={cfg.S:.3f} chance={cfg.chance:.3f}")

    cache = run_phase_a(cfg, device)

    seeds = cfg.seeds
    print(f"unigram inductable-acc {cache['unigram_acc']:.3f}  max_marginal {cache['max_marginal']:.3f}  "
          f"random-init {cache['random_init_acc']:.3f}")
    for d in cfg.depths:
        line = "  ".join(f"w{w}:{sum(cache['clean'][f'd{d}w{w}'][s]['acc'] for s in seeds)/len(seeds):.2f}"
                         for w in cfg.widths)
        print(f"depth{d} clean acc: {line}")
    sc = "  ".join(f"w{w}:{sum(cache['shortcut'][f'w{w}'][s]['acc'] for s in seeds)/len(seeds):.2f}"
                   for w in cfg.shortcut_widths)
    print(f"1L fixed-offset (shortcut) acc: {sc}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
