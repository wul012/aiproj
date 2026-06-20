"""v1197 Phase A: train clean 2-layer induction models and cache head scores + ablation results.

Per seed: train a 2-layer width-64 n_head=8 model on v1196's clean induction task; classify heads
by attention pattern; cache base accuracy, per-head prev/induction scores, top-k/bottom-k/single
MEAN- and ZERO-ablation accuracies (enabling the Phase-B tau-robustness sweep), and the
composition attentions (prev-ablation vs matched non-prev-L0 control, on a SEPARATE batch). No
verdict logic here -- Phase B re-derives it with zero retrain.

Example:
    python scripts/run_induction_circuit_v1197.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.induction_circuit_v1197 import CircuitConfig, run_phase_a  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1197 Phase A: induction-circuit dissection, save cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "induction-circuit-v1197" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--seeds", type=int, default=5)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(1337)
    device = choose_device(args.device)
    cfg = CircuitConfig(seeds=tuple(1337 + i for i in range(args.seeds)))
    print(f"device={device} K={cfg.K} T={cfg.T} width={cfg.width} n_head={cfg.n_head} "
          f"depth={cfg.depth} seeds={cfg.seeds} S={cfg.S:.3f}")

    cache = run_phase_a(cfg, device)

    print(f"unigram acc {cache['unigram_acc']:.3f}  chance {cache['chance']:.3f}")
    for s in cfg.seeds:
        r = cache["seeds"][s]
        nprev = sum(1 for h in range(cfg.n_head) if r["prev"][f"0,{h}"] > cfg.tau_prev)
        nind = sum(1 for h in range(cfg.n_head) if r["ind"][f"1,{h}"] > cfg.tau_ind)
        kp, ki = r["composition"]["kp"], r["composition"]["ki"]
        print(f"  seed {s}: base {r['base_acc']:.3f} | prev-heads {nprev} ind-heads {nind} | "
              f"ablate-all-prev(mean) {r['mean_topprev'][kp]:.3f} ablate-all-ind(mean) {r['mean_topind'][ki]:.3f} | "
              f"control(mean) prev {r['mean_botprev'][kp]:.3f} ind {r['mean_botind'][ki]:.3f}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
