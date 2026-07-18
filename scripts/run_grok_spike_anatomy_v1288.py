"""v1288 Phase A: nine branch cells (wd=1 vs wd=0 arms) + two un-censor runs.

Example:
    python scripts/run_grok_spike_anatomy_v1288.py            # full plan
    python scripts/run_grok_spike_anatomy_v1288.py --probe    # P2: (4e-3, 1337)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_spike_anatomy_v1288 import (  # noqa: E402
    SpikeAnatomyConfig,
    episodes,
    run_cell,
    run_phase_a,
)

PROBE = (4e-3, 1337)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1288 Phase A trainer")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-spike-anatomy-v1288")
    parser.add_argument("--probe", action="store_true",
                        help="P2 probe: branch + both arms for lr=4e-3, 1337")
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = SpikeAnatomyConfig()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.probe:
        k_branch, horizon = next((k, h) for lr, seed, k, h in cfg.cells
                                 if (lr, seed) == PROBE)
        cell = run_cell(cfg, PROBE[0], PROBE[1], k_branch, horizon, device)
        torch.save(cell, args.out_dir / "p2_probe.pt")
        print(f"probe lr={PROBE[0]} seed={PROBE[1]} k_branch={k_branch}"
              f" branch_train={cell['branch_train']}"
              f" branch_val={cell['branch_val']}")
        for key in ("wd1", "wd0"):
            arm = cell["arms"][key]
            eps = episodes(arm["curve"], cfg.spike_bar)
            print(f"  {key}: episodes={eps}"
                  f" min_val={min(r[2] for r in arm['curve'])}"
                  f" heldout={arm['heldout_acc']} norm={arm['norm']:.3f}")
        return
    probe_path = args.out_dir / "p2_probe.pt"
    preloaded = (torch.load(probe_path, weights_only=False),) \
        if probe_path.exists() else ()
    cache = run_phase_a(cfg, device, preloaded=preloaded)
    torch.save(cache, args.out_dir / "phase_a_cache.pt")
    for c in cache["cells"]:
        n1 = len(episodes(c["arms"]["wd1"]["curve"], cfg.spike_bar))
        n0 = len(episodes(c["arms"]["wd0"]["curve"], cfg.spike_bar))
        print(f"lr={c['lr']} seed={c['seed']}: branch_val={c['branch_val']}"
              f" spikes wd1={n1} wd0={n0}")
    for e in cache["uncensor"]:
        print(f"uncensor lr={e['lr']} seed={e['seed']}:"
              f" final_val={e['curve'][-1][2]} heldout={e['heldout_acc']}")
    print(f"runs={cache['runs']} total_steps={cache['total_steps']}")
    print(f"cache={args.out_dir / 'phase_a_cache.pt'}")


if __name__ == "__main__":
    main()
