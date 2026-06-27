"""v1200 Phase B: CPU-only analysis over the cached wd-rescue dose-response (no training).

Loads the Phase-A cache, re-derives the verdict (does wd rescue generalization beyond the strong
early-stopping baseline? is it noise rejection via the flip-mask dissociation? is the rescue
noise-specific via difference-in-differences vs the eta=0 control?) + the wd-grid robustness check,
and writes the 5-format readability artifacts. Zero retrain (reuse-cached).

Example:
    python scripts/analyze_wd_noise_v1200.py
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

from minigpt.wd_noise_v1200 import WDConfig, build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "wd_noise_v1200"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1200 Phase B: wd-rescue analysis over the cache.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "wd-noise-v1200" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "wd-noise-v1200")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    c = cache["config"]
    cfg = WDConfig(L=c["L"], n_train=c["n_train"], width=c["width"], etas=tuple(c["etas"]),
                   wd_grid=tuple(c["wd_grid"]), seeds=tuple(c["seeds"]), lr=c["lr"],
                   steps=c["steps"], rec_every=c["rec_every"])
    print(f"loaded {args.cache}  (seeds={c['seeds']}, wd_grid={c['wd_grid']})")

    result = summarize(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    f = info["flags"]
    print(f"\nsubstrate_ok {f['substrate_ok']} | reference_memorized {f['reference_memorized']} | "
          f"converged {f['converged']} | seeds {f['n_seeds']} | robust {f['robust']}")
    print(f"RESCUE: best_wd={f['best_wd']} converged {f['best_wd_converged_err']} vs wd=0 early-stop "
          f"{f['wd0_earlystop_err']} (gap {f['rescue_gap']}) -> rescue {f['rescue']}")
    print(f"MECHANISM: acc_clean_subset {f['best_wd_acc_clean_subset']} | fit_to_noise {f['best_wd_fit_to_noise']} "
          f"| train_acc {f['best_wd_train_acc']} -> dissociation {f['dissociation']}")
    print(f"ATTRIBUTION: DiD {f['did']} -> did_ok {f['did_ok']} | interior_optimum {f['interior']} | "
          f"logit_norm {f['wd0_logit_norm']}->{f['best_wd_logit_norm']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
