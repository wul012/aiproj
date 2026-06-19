"""v1193 Phase A: run all continual-learning training arms ONCE and save the result cache.

The single training pass. Trains (per seed): consolidate A -> {naive=replay0, replay sweep,
random-label-B, continue-on-A, wrong-replay} branched from the SAME consolidated init, plus
a multitask-joint upper bound and a savings/relearning probe. Logs accuracies + acc_A
trajectories to one cache so Phase B (analyze_continual_v1193.py) re-derives the verdict
with NO retrain (the v1185-train -> v1186/88/91-analyze precedent).

Example:
    python scripts/run_continual_v1193.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.continual_v1193 import ContinualConfig, run_phase_a   # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1193 Phase A: train continual-learning arms, save cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "continual-v1193" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--p", type=int, default=23)
    p.add_argument("--task-a", default="add")
    p.add_argument("--task-b", default="mul")
    p.add_argument("--seeds", type=int, default=3)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(1337)
    device = choose_device(args.device)
    cfg = ContinualConfig(p=args.p, task_a=args.task_a, task_b=args.task_b,
                          seeds=tuple(1337 + i for i in range(args.seeds)))
    print(f"device={device} p={cfg.p} A={cfg.task_a} B={cfg.task_b} seeds={cfg.seeds} "
          f"b_budget={cfg.b_budget} replay={cfg.replay_buffer_sizes}")

    cache = run_phase_a(cfg, device)

    # quick console readout
    seeds = list(cache["accA_plateau"])
    plat = sum(cache["accA_plateau"].values()) / len(seeds)
    naive = sum(cache["naive"][s]["accA_after_B"] for s in seeds) / len(seeds)
    print(f"A plateau {plat:.3f} -> after B {naive:.3f} (chance {cache['chance']:.3f}); "
          f"leak_free={cache['leak_free']} B_majority_prior={cache['b_majority_prior']:.3f}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
