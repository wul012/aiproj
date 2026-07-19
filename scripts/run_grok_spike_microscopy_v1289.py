"""v1289 Phase A: nine faithful re-runs with dense in-window microscopy.

Example:
    python scripts/run_grok_spike_microscopy_v1289.py            # full plan
    python scripts/run_grok_spike_microscopy_v1289.py --probe    # P2: (8e-3, 1338)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_spike_microscopy_v1289 import (  # noqa: E402
    SpikeMicroscopyConfig,
    dense_episodes,
    dense_run,
    run_phase_a,
)

PROBE = (8e-3, 1338)
REFERENCE = ROOT / "f" / "1287" / "解释" / "grok_purification_v1287" / "phase_a_cache.pt"


def _prefix_mismatches(cell: dict, reference: Path) -> int:
    ref = torch.load(reference, weights_only=False)
    rc = next(c for c in ref["cells"]
              if (c["lr"], c["seed"]) == (cell["lr"], cell["seed"]))
    by_step = {int(r[0]): r for r in rc["curve"]}
    bad = 0
    for step, train, val in cell["coarse"]:
        row = by_step.get(int(step))
        if row is None or abs(row[1] - train) > 1e-9 \
                or abs(row[2] - val) > 1e-9:
            bad += 1
    return bad


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1289 Phase A trainer")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-spike-microscopy-v1289")
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--probe", action="store_true",
                        help="P2 probe: dense re-run of lr=8e-3, seed 1338")
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = SpikeMicroscopyConfig()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.probe:
        rerun_end, windows = next(
            (r, w) for lr, seed, r, w in cfg.cells if (lr, seed) == PROBE)
        t0 = time.time()
        cell = dense_run(cfg, PROBE[0], PROBE[1], rerun_end, windows, device)
        wall = time.time() - t0
        torch.save(cell, args.out_dir / "p2_probe.pt")
        bad = _prefix_mismatches(cell, args.reference)
        print(f"probe lr={PROBE[0]} seed={PROBE[1]} rerun_end={rerun_end}"
              f" wall={wall:.1f}s prefix_mismatches={bad}")
        total = sum(r for _l, _s, r, _w in cfg.cells)
        dense_total = sum(w1 - w0 + 1 for _l, _s, _r, ws in cfg.cells
                          for w0, w1 in ws)
        probe_dense = sum(w1 - w0 + 1 for w0, w1 in windows)
        rate = wall / (rerun_end + probe_dense)
        print(f"projected_full_phase_a={(total + dense_total) * rate / 60:.1f}"
              f"min (stop bar 180min)")
        for block in cell["dense"]:
            eps = dense_episodes(block, cfg.spike_bar)
            interior = [e for e in eps
                        if not e["censored"] and e["start"] > block["w0"]
                        and e["end"] < block["w1"]]
            print(f"  window [{block['w0']},{block['w1']}]: episodes="
                  f"{[(e['start'], e['end'], round(e['min_val'], 3)) for e in eps]}"
                  f" interior_deep={sum(1 for e in interior if e['min_val'] < 0.5)}")
        return
    probe_path = args.out_dir / "p2_probe.pt"
    preloaded = (torch.load(probe_path, weights_only=False),) \
        if probe_path.exists() else ()
    cache = run_phase_a(cfg, device, preloaded=preloaded)
    torch.save(cache, args.out_dir / "phase_a_cache.pt")
    for c in cache["cells"]:
        n_ep = sum(len(dense_episodes(b, cfg.spike_bar)) for b in c["dense"])
        deepest = min(min(b["val_acc"]) for b in c["dense"])
        print(f"lr={c['lr']} seed={c['seed']}: rerun_end={c['rerun_end']}"
              f" windows={len(c['dense'])} episodes={n_ep}"
              f" dense_min_val={deepest:.3f}")
    print(f"runs={cache['runs']} total_steps={cache['total_steps']}")
    print(f"cache={args.out_dir / 'phase_a_cache.pt'}")


if __name__ == "__main__":
    main()
