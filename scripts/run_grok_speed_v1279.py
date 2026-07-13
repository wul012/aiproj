"""v1279 Phase A: train the width grid + init-scale arms once and cache metrics.

Example:
    python scripts/run_grok_speed_v1279.py            # full 24-cell plan
    python scripts/run_grok_speed_v1279.py --probe    # P2: width 64, seed 1337
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_speed_v1279 import SpeedConfig, run_phase_a, train_cell  # noqa: E402


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1279 Phase A trainer")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "grok-speed-v1279")
    parser.add_argument("--probe", action="store_true", help="P2 probe: one run at width 64")
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = SpeedConfig()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.probe:
        cell = train_cell(cfg, 64, cfg.seeds[0], 1.0, device)
        torch.save(cell, args.out_dir / "p2_probe.pt")
        print(f"probe width=64 seed={cfg.seeds[0]} heldout={cell['heldout_acc']}"
              f" t_gen={cell['t_gen']} n0={cell['n0']}")
        return
    cache = run_phase_a(cfg, device)
    torch.save(cache, args.out_dir / "phase_a_cache.pt")
    for cell in cache["cells"]:
        print(f"{cell['arm']} w={cell['width']} seed={cell['seed']} a={cell['alpha']:.3f}"
              f" heldout={cell['heldout_acc']} t_gen={cell['t_gen']}")
    print(f"cache={args.out_dir / 'phase_a_cache.pt'}")


if __name__ == "__main__":
    main()
