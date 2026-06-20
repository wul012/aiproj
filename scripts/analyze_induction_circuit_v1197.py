"""v1197 Phase B: CPU-only analysis over the cached induction-circuit results (no training).

Loads the Phase-A cache, re-derives the necessity/specificity/composition/redundancy verdict
(MEAN-ablation primary, zero-ablation agreement) + the tau-robustness sweep, and writes the
5-format readability artifacts. Re-derivable with zero retrain (reuse-cached).

Example:
    python scripts/analyze_induction_circuit_v1197.py
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

from minigpt.induction_circuit_v1197 import CircuitConfig, build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "induction_circuit_v1197"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1197 Phase B: induction-circuit analysis over the cache.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "induction-circuit-v1197" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "induction-circuit-v1197")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    c = cache["config"]
    cfg = CircuitConfig(K=c["K"], T=c["T"], width=c["width"], depth=c["depth"], n_head=c["n_head"],
                        seeds=tuple(c["seeds"]), tau_prev=c["tau_prev"], tau_ind=c["tau_ind"])
    print(f"loaded {args.cache}  (n_head={cfg.n_head}, seeds={c['seeds']})")

    result = summarize(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    f = info["flags"]
    print(f"\nbase {f['base_acc']:.3f} | unigram {f['unigram_acc']:.3f} | usable_seed_frac {f['usable_seed_frac']}")
    print(f"NECESSITY ablate-prev(mean) {f['prev_ablate_acc_mean']:.3f} ablate-ind(mean) {f['ind_ablate_acc_mean']:.3f} "
          f"(zero {f['prev_ablate_acc_zero']:.3f}/{f['ind_ablate_acc_zero']:.3f}) -> {f['necessity']}")
    print(f"SPECIFICITY control-prev {f['prev_control_acc']:.3f} control-ind {f['ind_control_acc']:.3f} -> {f['specificity']}")
    print(f"REDUNDANCY prev single/class drop {f.get('prev_max_single_drop')}/{f.get('prev_class_drop')} "
          f"ind {f.get('ind_max_single_drop')}/{f.get('ind_class_drop')} -> prev_red {f['prev_redundant']} ind_red {f['ind_redundant']}")
    print(f"COMPOSITION drop prev {f['comp_drop_prev']:.3f} vs nonprev-control {f['comp_drop_nonprev_control']:.3f} -> {f['composition']}")
    print(f"tau_grid_agree_frac {f['tau_grid_agree_frac']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
