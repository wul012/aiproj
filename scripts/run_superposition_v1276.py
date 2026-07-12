"""v1276 Phase A: run CPU probes or resume them into the full grid."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.superposition_v1276 import (  # noqa: E402
    SuperConfig,
    all_cells,
    analyze,
    probe_cells,
    probe_ready,
    run_phase_a,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the preregistered CPU-only v1276 experiment.")
    parser.add_argument("--mode", choices=("probe", "full"), required=True)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=1)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.threads < 1:
        raise SystemExit("--threads must be positive")
    torch.set_num_threads(args.threads)
    cfg = SuperConfig()
    prior = torch.load(args.resume, map_location="cpu", weights_only=False) if args.resume else None
    if args.mode == "full":
        if prior is None:
            raise SystemExit("full mode requires --resume with the committed probe cache")
        if not probe_ready(prior, cfg):
            raise SystemExit("sparse probe did not show packing in both arms; re-panel before full grid")
        targets = all_cells(cfg)
    else:
        if prior is not None:
            raise SystemExit("probe mode does not accept --resume")
        targets = probe_cells(cfg)
    cache = run_phase_a(cfg, cells=targets, prior=prior)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    result = analyze(cache, cfg)
    for row in result["rows"]:
        if args.mode == "probe" or row["seed"] == cfg.seeds[0]:
            print(
                f"arm={row['arm']} S={row['sparsity']} seed={row['seed']} converged={row['converged']} "
                f"loss={row['final_loss']:.8f} baseline={row['dedicated_loss']:.8f} "
                f"R={row['represented']} drift={row['plateau_drift']:.6f}"
            )
    print(f"mode={args.mode} cpu_threads={args.threads} cells={len(cache['cells'])} saved={args.out}")
    if args.mode == "probe":
        print(f"probe_ready={probe_ready(cache, cfg)}")


if __name__ == "__main__":
    main()
