"""v1283 Phase A: train the boundary widths {20, 24, 28} + anchors once and cache.

Example:
    python scripts/run_grok_delay_gate_v1283.py            # full plan (13 runs)
    python scripts/run_grok_delay_gate_v1283.py --probe    # P2: w=24, seed 1337
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_delay_gate_v1283 import DelayGateConfig, run_phase_a  # noqa: E402
from minigpt.grok_init_rescue_v1280 import train_cell  # noqa: E402


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1283 Phase A trainer")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-delay-gate-v1283")
    parser.add_argument("--probe", action="store_true",
                        help="P2 probe: one run at width 24, seed 1337")
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = DelayGateConfig()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.probe:
        width = cfg.boundary_widths[1]
        cell = train_cell(replace(cfg, width=width), 1.0, cfg.lr,
                          cfg.seeds[0], device) | {"width": width}
        torch.save(cell, args.out_dir / "p2_probe.pt")
        print(f"probe width={width} seed={cfg.seeds[0]}"
              f" heldout={cell['heldout_acc']} t_mem={cell['t_mem']}"
              f" t_gen={cell['t_gen']}")
        return
    probe_path = args.out_dir / "p2_probe.pt"
    preloaded = (torch.load(probe_path, weights_only=False),) if probe_path.exists() else ()
    cache = run_phase_a(cfg, device, preloaded=preloaded)
    torch.save(cache, args.out_dir / "phase_a_cache.pt")
    for c in cache["cells"]:
        print(f"{c['arm']} w={c['width']} seed={c['seed']}"
              f" heldout={c['heldout_acc']} t_mem={c['t_mem']} t_gen={c['t_gen']}")
    print(f"cache={args.out_dir / 'phase_a_cache.pt'}")


if __name__ == "__main__":
    main()
