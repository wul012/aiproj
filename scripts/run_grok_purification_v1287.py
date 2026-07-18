"""v1287 Phase A: the eleven post-grok extension cells (full + ladders).

Example:
    python scripts/run_grok_purification_v1287.py            # full plan
    python scripts/run_grok_purification_v1287.py --probe    # P2: (8e-3, 1337)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_circuit_timing_v1284 import set_share  # noqa: E402
from minigpt.grok_purification_v1287 import (  # noqa: E402
    PurificationConfig,
    run_cell,
    run_phase_a,
)

PROBE = (8e-3, 1337, 1000)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="v1287 Phase A trainer")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "output" / "grok-purification-v1287")
    parser.add_argument("--reference", type=Path,
                        default=ROOT / "f" / "1286" / "解释"
                        / "grok_lr_compression_v1286" / "phase_a_cache.pt",
                        help="committed cache holding the probe cell's anchor")
    parser.add_argument("--probe", action="store_true",
                        help="P2 probe: the full extension for lr=8e-3, 1337")
    args = parser.parse_args(argv)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = PurificationConfig()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.probe:
        lr, seed, t_gen_ref = PROBE
        cell = run_cell(cfg, lr, seed, t_gen_ref, device)
        torch.save(cell, args.out_dir / "p2_probe.pt")
        reference = torch.load(args.reference, weights_only=False)
        ref = next(c for c in reference["cells"]
                   if (c["lr"], c["seed"]) == (lr, seed))
        print(f"probe lr={lr} seed={seed} steps_run={cell['steps_run']}"
              f" (horizon {cell['ladder'][-1]}) prefix_ok={cell['prefix_ok']}"
              f" t_mem={cell['t_mem']} t_gen={cell['t_gen']}"
              f" heldout={cell['heldout_acc']}")
        print(f"  anchor(cached final_share)={ref['final_share']}")
        for s in cell["snapshots"]:
            print(f"  k={s['k']} val={s['val_acc']}"
                  f" C_ref={set_share(s['power'], ref['top5']):.6f}"
                  f" prefix_ok={s['prefix_ok']}")
        print(f"  k={cell['steps_run']} (final)"
              f" C_ref={set_share(cell['final_power'], ref['top5']):.6f}")
        return
    probe_path = args.out_dir / "p2_probe.pt"
    preloaded = (torch.load(probe_path, weights_only=False),) \
        if probe_path.exists() else ()
    cache = run_phase_a(cfg, device, preloaded=preloaded)
    torch.save(cache, args.out_dir / "phase_a_cache.pt")
    for c in cache["cells"]:
        print(f"lr={c['lr']} seed={c['seed']}: prefix_ok={c['prefix_ok']}"
              f" steps_run={c['steps_run']} t_mem={c['t_mem']}"
              f" t_gen={c['t_gen']} heldout={c['heldout_acc']}")
    print(f"runs={cache['runs']} total_steps={cache['total_steps']}")
    print(f"cache={args.out_dir / 'phase_a_cache.pt'}")


if __name__ == "__main__":
    main()
