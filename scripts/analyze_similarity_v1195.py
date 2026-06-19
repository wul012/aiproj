"""v1195 Phase B: CPU-only analysis over the cached similarity sweep (no training).

Loads the Phase-A cache, computes the analytic-overlap collapse curve + confound controls +
verdict, and writes the 5-format readability artifacts. Re-derivable with zero retrain.

Example:
    python scripts/analyze_similarity_v1195.py
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

from minigpt.similarity_v1195 import SimilarityConfig, build_report, decide, summarize  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "similarity_v1195"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1195 Phase B: similarity-forgetting analysis over the cache.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "similarity-v1195" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "similarity-v1195")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    cfg = SimilarityConfig()
    cfg = SimilarityConfig(base=type(cfg.base)(p=cache["config"]["p"]),
                           seeds=tuple(cache["config"]["seeds"]),
                           mixture_ss=tuple(cache["config"]["mixture_ss"]),
                           type_funcs=tuple(cache["config"]["type_funcs"]),
                           add_offset_c0=cache["config"]["add_offset_c0"])
    print(f"loaded {args.cache}  (p={cfg.p}, seeds={cache['config']['seeds']})")

    result = summarize(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print(f"\nA plateau {result['plateau'][0]:.3f} | continue-on-A floor {result['continue_on_A_forget'][0]:.3f} | "
          f"joint A{result['joint_accA'][0]:.2f}/B{result['joint_accB'][0]:.2f}")
    print("overlap -> forgetting (test-cell overlap):")
    for k in result["mix_keys"] + result["type_keys"]:
        m = result["stats"][k]
        learned = "learned" if m["learned"] else "UNLEARNED"
        accb = m["accB_conflict"][0]
        print(f"  {k:<18} overlap={m['overlap'][0]:.3f}  forget={m['forget'][0]:.3f}±{m['forget'][1]:.3f}  "
              f"accB_conf={accb:.3f}  drift={m['emb_drift'][0]:.2f}  [{learned}]")
    print(f"Spearman(overlap,forget)={info['flags']['spearman_overlap_forget']} "
          f"(perm p={info['flags']['spearman_perm_p']}); superlinear excess={info['flags']['mean_superlinear_excess']}")
    print("residuals:", json.dumps(info["flags"]["residuals"], ensure_ascii=True))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
