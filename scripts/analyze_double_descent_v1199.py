"""v1199 Phase B: CPU-only analysis over the cached double-descent sweeps (no training).

Loads the Phase-A cache, re-derives the verdict (model-size second descent? epoch-wise recovery?
signal-before-noise?) with the validity gates + interpolation-tau robustness, and writes the
5-format readability artifacts. Zero retrain (reuse-cached).

Example:
    python scripts/analyze_double_descent_v1199.py
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

from minigpt.double_descent_v1199 import DDConfig, build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "double_descent_v1199"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1199 Phase B: double-descent analysis over the cache.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "double-descent-v1199" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "double-descent-v1199")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    c = cache["config"]
    cfg = DDConfig(L=c["L"], n_train=c["n_train"], etas=tuple(c["etas"]), widths=tuple(c["widths"]),
                   epoch_widths=tuple(c["epoch_widths"]), seeds=tuple(c["seeds"]),
                   tau_interp=c["tau_interp"], epoch_steps=c["epoch_steps"], rec_every=c["rec_every"])
    print(f"loaded {args.cache}  (seeds={c['seeds']}, widths={c['widths']})")

    result = summarize(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    f = info["flags"]
    print(f"\nctrl_ok {f['ctrl_ok']} | interp_reached {f['interp_reached']} (w_interp={f['w_interp']}) | "
          f"seeds {f['n_seeds']} | tau_grid_agree {f['tau_grid_agree_frac']}")
    print(f"MODEL-SIZE: peak w={f['ms_peak_w']} test_err {f['ms_test_err_at_peak']} | widest {f['ms_test_err_widest']} "
          f"-> second_descent {f['ms_second_descent']}")
    print(f"EPOCH-WISE (w={f['epoch_width']}): best_pre {f['epoch_best_pre']} -> final {f['epoch_final']} "
          f"(rise {f['epoch_rise']}, ctrl rise {f['epoch_rise_ctrl']}) recovery {f['epoch_recovery']} "
          f"-> epoch_dd {f['epoch_dd']}, signal_before_noise {f['signal_before_noise']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
