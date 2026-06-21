"""v1199 Phase A: train the double-descent sweeps and cache every trajectory (no verdict logic).

Model-size arm: per (eta, width, seed) train a 1-layer n_head=1 MiniGPT to interpolation on a fixed
noisy-halfspace train set, cache final train acc + clean test error. Epoch-wise arm: per
(eta, width, seed) record the clean test-error trajectory vs training step. Phase B re-derives the
verdict with zero retrain.

Example:
    python scripts/run_double_descent_v1199.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.double_descent_v1199 import DDConfig, run_phase_a  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1199 Phase A: double-descent sweeps, save cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "double-descent-v1199" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--seeds", type=int, default=5)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(1337)
    device = choose_device(args.device)
    cfg = DDConfig(seeds=tuple(range(args.seeds)))
    print(f"device={device} L={cfg.L} n_train={cfg.n_train} etas={cfg.etas} widths={cfg.widths} "
          f"epoch_widths={cfg.epoch_widths} seeds={cfg.seeds}")

    cache = run_phase_a(cfg, device)

    # quick console digest per eta
    for eta in cfg.etas:
        line = f"  eta={eta}: model-size test_err " + " ".join(
            f"w{w}:{sum(cache['model_size'][f'{eta}|{w}|{s}']['test_err'] for s in cfg.seeds)/len(cfg.seeds):.3f}"
            f"(tr{sum(cache['model_size'][f'{eta}|{w}|{s}']['train_acc'] for s in cfg.seeds)/len(cfg.seeds):.2f})"
            for w in cfg.widths)
        print(line)
        for w in cfg.epoch_widths:
            finals = [cache['epoch'][f'{eta}|{w}|{s}']['traj'][-1][2] for s in cfg.seeds]
            print(f"    epoch w{w}: final test_err {sum(finals)/len(finals):.3f}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
