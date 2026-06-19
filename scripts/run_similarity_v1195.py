"""v1195 Phase A: run the task-similarity / output-overlap forgetting sweep ONCE, save the cache.

Per seed: consolidate A=(a+b) mod p to a plateau (reused), then from that init train each B-arm
-- the TYPE family {add_same, add_offset, linear, mul, rand} and the MIXTURE s-grid -- for a
fixed budget, logging A-forgetting, accB split into conflict/overlap cells, B-train memorization,
and the shared number-embedding drift; plus a continue-on-A floor and the canonical add+mul joint
upper bound. No verdict logic (Phase B re-derives from the cache with zero retrain).

Example:
    python scripts/run_similarity_v1195.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.continual_v1193 import ContinualConfig          # noqa: E402
from minigpt.similarity_v1195 import SimilarityConfig, run_phase_a  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything   # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1195 Phase A: task-similarity forgetting sweep, save cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "similarity-v1195" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--p", type=int, default=23)
    p.add_argument("--seeds", type=int, default=5)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(1337)
    device = choose_device(args.device)
    base = ContinualConfig(p=args.p, task_a="add", task_b="mul", train_frac=0.8, weight_decay=0.5,
                           plateau_acc=0.98, plateau_hold=5, consolidate_max_steps=6000,
                           b_budget=1500, b_eval_every=100)
    cfg = SimilarityConfig(base=base, seeds=tuple(1337 + i for i in range(args.seeds)))
    print(f"device={device} p={cfg.p} seeds={cfg.seeds} b_budget={base.b_budget} "
          f"types={cfg.type_funcs} mixture_ss={cfg.mixture_ss}")

    cache = run_phase_a(cfg, device)

    seeds = list(cache["plateau"])
    plat = sum(cache["plateau"].values()) / len(seeds)
    print(f"A plateau {plat:.3f} (chance {cache['chance']:.3f}); leak_free={cache['leak_free']}")
    for k in sorted(cache["arms"]):
        f = sum(cache["plateau"][s] - cache["arms"][k][s]["accA_after_B"] for s in seeds) / len(seeds)
        ov = sum(cache["overlaps"][k][s][2] for s in seeds) / len(seeds)
        print(f"  {k:<18} overlap_test={ov:.3f}  forgetting={f:.3f}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
