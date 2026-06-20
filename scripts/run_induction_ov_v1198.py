"""v1198 Phase A: train clean 2-layer induction models and cache OV-copying + DLA results.

Per seed: train a 2-layer width-64 n_head=4 model on v1196's clean induction task; classify heads
by attention pattern; cache base accuracy, per-head prev/induction scores, per-head weight-level OV
copying scores (copy_z, diag_is_max), per-head activation Direct Logit Attribution gaps, and the
tied-embedding Gram baseline. No verdict logic here -- Phase B re-derives it with zero retrain.

Example:
    python scripts/run_induction_ov_v1198.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.induction_ov_v1198 import OVConfig, run_phase_a  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1198 Phase A: induction OV-copying, save cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "induction-ov-v1198" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--seeds", type=int, default=8)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(1337)
    device = choose_device(args.device)
    cfg = OVConfig(seeds=tuple(1337 + i for i in range(args.seeds)))
    print(f"device={device} K={cfg.K} T={cfg.T} width={cfg.width} n_head={cfg.n_head} "
          f"depth={cfg.depth} seeds={cfg.seeds} S={cfg.S:.3f}")

    cache = run_phase_a(cfg, device)

    print(f"unigram acc {cache['unigram_acc']:.3f}  chance {cache['chance']:.3f}")
    for s in cfg.seeds:
        r = cache["seeds"][s]
        nind = sum(1 for h in range(cfg.n_head) if r["ind"][f"1,{h}"] > cfg.tau_ind)
        ind_h = [h for h in range(cfg.n_head) if r["ind"][f"1,{h}"] > cfg.tau_ind]
        ctrl_h = [h for h in range(cfg.n_head) if r["ind"][f"1,{h}"] <= cfg.tau_ind]
        icz = sum(r["copy_z"][f"1,{h}"] for h in ind_h) / max(len(ind_h), 1)
        ccz = sum(r["copy_z"][f"1,{h}"] for h in ctrl_h) / max(len(ctrl_h), 1)
        idg = sum(r["dla_gap"][f"1,{h}"] for h in ind_h) / max(len(ind_h), 1)
        print(f"  seed {s}: base {r['base_acc']:.3f} | ind-heads {nind} | "
              f"copy_z ind {icz:+.2f} ctrl {ccz:+.2f} (gram {r['gram_copy_z']:+.2f}) | "
              f"DLA_gap ind {idg:+.3f}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
