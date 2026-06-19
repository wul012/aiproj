"""v1194 Phase A: train the EWC and replay stability-plasticity frontiers ONCE, save the cache.

Per seed: consolidate A, estimate the diagonal Fisher, then map the EWC-lambda frontier and the
replay-buffer frontier (acc_A, acc_B at each knob), plus an EWC+replay hybrid, a continue-on-A
floor, and a multitask-joint upper bound. Phase B re-derives the verdict with no retrain.

Example:
    python scripts/run_ewc_replay_v1194.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.continual_v1193 import ContinualConfig                  # noqa: E402
from minigpt.ewc_replay_v1194 import EWCReplayConfig, run_phase_a    # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything    # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1194 Phase A: EWC vs replay frontiers, save cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "ewc-replay-v1194" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--p", type=int, default=23)
    p.add_argument("--seeds", type=int, default=3)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(1337)
    device = choose_device(args.device)
    cfg = EWCReplayConfig(base=ContinualConfig(p=args.p, task_a="add", task_b="mul"),
                          seeds=tuple(1337 + i for i in range(args.seeds)))
    print(f"device={device} p={args.p} seeds={cfg.seeds} lambdas={cfg.ewc_lambdas} ks={cfg.replay_ks}")

    cache = run_phase_a(cfg, device)

    seeds = list(cache["accA_plateau"])
    plat = sum(cache["accA_plateau"].values()) / len(seeds)
    print(f"A plateau {plat:.3f}; leak_free={cache['leak_free']} B_majority_prior={cache['b_majority_prior']:.3f}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
