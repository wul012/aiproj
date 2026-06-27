"""v1200 Phase A: train the weight-decay dose-response under label noise and cache trajectories.

Per (eta, wd, seed): from ONE per-seed (teacher, data, flip-mask, init), train a fixed-budget
overparameterized MiniGPT at each weight_decay (within-seed paired), and cache the clean-test-error
trajectory + final flip-mask metrics (acc_clean_subset, fit_to_noise) + logit norm + the flip indices.
No verdict logic here -- Phase B re-derives it with zero retrain.

Example:
    python scripts/run_wd_noise_v1200.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.wd_noise_v1200 import WDConfig, run_phase_a  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1200 Phase A: wd-rescue dose-response, save cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "wd-noise-v1200" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--seeds", type=int, default=5)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(1337)
    device = choose_device(args.device)
    cfg = WDConfig(seeds=tuple(range(args.seeds)))
    print(f"device={device} L={cfg.L} N={cfg.n_train} width={cfg.width} etas={cfg.etas} "
          f"wd_grid={cfg.wd_grid} seeds={cfg.seeds} steps={cfg.steps}")

    cache = run_phase_a(cfg, device)

    eta = cfg.noise_eta
    print(f"\neta={eta} dose-response (mean over seeds):")
    for wd in cfg.wd_grid:
        ce = sum(cache["arms"][f"{eta}|{wd}|{s}"]["test_err"] for s in cfg.seeds) / len(cfg.seeds)
        tr = sum(cache["arms"][f"{eta}|{wd}|{s}"]["final_train_acc"] for s in cfg.seeds) / len(cfg.seeds)
        fn = sum(cache["arms"][f"{eta}|{wd}|{s}"]["fit_to_noise"] for s in cfg.seeds) / len(cfg.seeds)
        ac = sum(cache["arms"][f"{eta}|{wd}|{s}"]["acc_clean_subset"] for s in cfg.seeds) / len(cfg.seeds)
        print(f"  wd={wd:>5}: test_err(final) {ce:.3f} | train_acc {tr:.3f} | acc_clean {ac:.3f} | fit_noise {fn:.3f}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
