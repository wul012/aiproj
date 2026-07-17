"""v1286 Phase A: the eight compressed d=128 trajectory cells (full + ladders).

Example:
    python scripts/run_grok_lr_compression_v1286.py            # full plan
    python scripts/run_grok_lr_compression_v1286.py --probe    # P2: (4e-3, 1337)
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_circuit_timing_v1284 import run_cell  # noqa: E402
from minigpt.grok_lr_compression_v1286 import LrCompressionConfig, run_phase_a  # noqa: E402


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1286 Phase A trainer")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-lr-compression-v1286")
    parser.add_argument("--probe", action="store_true",
                        help="P2 probe: the full ladder for lr=4e-3, seed 1337")
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = LrCompressionConfig()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.probe:
        cell = run_cell(replace(cfg, lr=4e-3), cfg.width, 1337, "delayed",
                        device) | {"lr": 4e-3}
        torch.save(cell, args.out_dir / "p2_probe.pt")
        print(f"probe lr=0.004 seed=1337 prefix_ok={cell['prefix_ok']}"
              f" t_mem={cell['t_mem']} t_gen={cell['t_gen']}"
              f" heldout={cell['heldout_acc']}"
              f" final_share={cell['final_share']} c0={cell['c0_share']}")
        for s in cell["snapshots"]:
            print(f"  k={s['k']} train={s['train_acc']} val={s['val_acc']}"
                  f" share={s['share']} prefix_ok={s['prefix_ok']}")
        return
    probe_path = args.out_dir / "p2_probe.pt"
    preloaded = (torch.load(probe_path, weights_only=False),) if probe_path.exists() else ()
    cache = run_phase_a(cfg, device, preloaded=preloaded)
    torch.save(cache, args.out_dir / "phase_a_cache.pt")
    for c in cache["cells"]:
        print(f"lr={c['lr']} seed={c['seed']}: prefix_ok={c['prefix_ok']}"
              f" t_mem={c['t_mem']} t_gen={c['t_gen']}"
              f" final_share={c['final_share']} snapshots={len(c['snapshots'])}")
    print(f"runs={cache['runs']} total_steps={cache['total_steps']}")
    print(f"cache={args.out_dir / 'phase_a_cache.pt'}")


if __name__ == "__main__":
    main()
