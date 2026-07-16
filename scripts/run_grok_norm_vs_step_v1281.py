"""v1281 Phase A: train the alpha=1 matched-step control cells once and cache.

Example:
    python scripts/run_grok_norm_vs_step_v1281.py            # full plan (10 runs)
    python scripts/run_grok_norm_vs_step_v1281.py --probe    # P2: alpha=1, lr=4e-3
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_init_rescue_v1280 import train_cell  # noqa: E402
from minigpt.grok_norm_vs_step_v1281 import StepClockConfig, run_phase_a  # noqa: E402


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1281 Phase A trainer")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-norm-vs-step-v1281")
    parser.add_argument("--probe", action="store_true",
                        help="P2 probe: one run at alpha=1, lr=4e-3, seed 1337")
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = StepClockConfig()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.probe:
        cell = train_cell(cfg, 1.0, cfg.verdict_lrs[0], cfg.verdict_seeds[0], device)
        torch.save(cell, args.out_dir / "p2_probe.pt")
        print(f"probe alpha=1 lr={cfg.verdict_lrs[0]} seed={cfg.verdict_seeds[0]}"
              f" heldout={cell['heldout_acc']} t_mem={cell['t_mem']}"
              f" t_gen={cell['t_gen']}")
        return
    probe_path = args.out_dir / "p2_probe.pt"
    preloaded = (torch.load(probe_path, weights_only=False),) if probe_path.exists() else ()
    cache = run_phase_a(cfg, device, preloaded=preloaded)
    torch.save(cache, args.out_dir / "phase_a_cache.pt")
    for c in cache["cells"]:
        print(f"{c['arm']} a={c['alpha']} lr={c['lr']} seed={c['seed']}"
              f" heldout={c['heldout_acc']} t_mem={c['t_mem']} t_gen={c['t_gen']}")
    print(f"cache={args.out_dir / 'phase_a_cache.pt'}")


if __name__ == "__main__":
    main()
