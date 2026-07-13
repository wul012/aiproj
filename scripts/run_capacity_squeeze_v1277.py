"""v1277 Phase A: train the width grid once and cache per-cell metrics.

Example:
    python scripts/run_capacity_squeeze_v1277.py                # full grid
    python scripts/run_capacity_squeeze_v1277.py --probe        # P2: width 16, seed 1337
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.capacity_squeeze_v1277 import SqueezeConfig, cell_metrics, run_phase_a, train_cell  # noqa: E402


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1277 Phase A trainer")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "capacity-squeeze-v1277")
    parser.add_argument("--probe", action="store_true", help="P2 probe: one run at width 16")
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = SqueezeConfig()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.probe:
        model, meta, _curve = train_cell(cfg, 16, cfg.seeds[0], device)
        cell = cell_metrics(model, meta, cfg)
        torch.save(cell, args.out_dir / "p2_probe.pt")
        print(f"probe width=16 seed={cfg.seeds[0]} heldout={cell['heldout_acc']}"
              f" t_gen={cell['t_gen']} steps={cell['steps_run']}")
        return
    cache = run_phase_a(cfg, device)
    torch.save(cache, args.out_dir / "phase_a_cache.pt")
    for cell in cache["cells"]:
        print(f"w={cell['width']} seed={cell['seed']} heldout={cell['heldout_acc']}"
              f" t_gen={cell['t_gen']}")
    print(f"cache={args.out_dir / 'phase_a_cache.pt'}")


if __name__ == "__main__":
    main()
