"""v1198 Phase B: CPU-only analysis over the cached induction OV-copying results (no training).

Loads the Phase-A cache, re-derives the two-prong copying verdict (weight-level OV copying +
activation DLA, which must AGREE), the Gram-confound-aware paired contrasts, and the tau-robustness
sweep, then writes the 5-format readability artifacts. Re-derivable with zero retrain (reuse-cached).

Example:
    python scripts/analyze_induction_ov_v1198.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.induction_ov_v1198 import OVConfig, build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "induction_ov_v1198"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1198 Phase B: induction OV-copying analysis over the cache.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "induction-ov-v1198" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "induction-ov-v1198")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    c = cache["config"]
    cfg = OVConfig(K=c["K"], T=c["T"], width=c["width"], depth=c["depth"], n_head=c["n_head"],
                   seeds=tuple(c["seeds"]), tau_prev=c["tau_prev"], tau_ind=c["tau_ind"])
    print(f"loaded {args.cache}  (n_head={cfg.n_head}, seeds={c['seeds']})")

    result = summarize(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    f = info["flags"]
    print(f"\nbase {f['base_acc']:.3f} | unigram {f['unigram_acc']:.3f} | classifiable_frac {f['classifiable_frac']}")
    print(f"PRONG 1 OV copy_z: ind {f['ind_copy_z']:+.2f} | ctrl {f['ctrl_copy_z']:+.2f} | prev {f['prev_copy_z']:+.2f} "
          f"| gram {f['gram_copy_z']:+.2f} | ind diag_is_max {f['ind_diag_is_max']:.2f} -> copy_ok {f['copy_ok']}")
    print(f"PRONG 2 DLA_gap:  ind {f['ind_dla_gap']:+.3f} | ctrl {f['ctrl_dla_gap']:+.3f} | prev {f['prev_dla_gap']:+.3f} "
          f"-> dla_ok {f['dla_ok']}")
    print(f"tau_grid_agree_frac {f['tau_grid_agree_frac']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
