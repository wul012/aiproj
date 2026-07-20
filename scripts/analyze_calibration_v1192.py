"""v1192 Phase B: CPU-only calibration analysis over the cached logits (no training).

Loads the Phase-A cache, fits the global temperature, computes analytic ECE/NLL/Brier/KL,
runs the specificity controls and decide(), and writes the 5-format readability artifacts.
Re-derivable with zero retrain (reuse-cached discipline; mirrors v1186/88/91 over v1185).

Example:
    python scripts/analyze_calibration_v1192.py
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

from minigpt.calibration_v1192 import CalibrationConfig, build_report, decide, run_analysis  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402

STEM = "calibration_v1192"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1192 Phase B: calibration analysis over cached logits.")
    p.add_argument("--cache", type=Path, default=ROOT / "output" / "calibration-v1192" / "cache.pt")
    p.add_argument("--out-dir", type=Path, default=ROOT / "output" / "calibration-v1192")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    cache = torch.load(args.cache, weights_only=False)
    print(f"loaded cache {args.cache}  (headline n={cache['headline_n']}, seeds={cache['meta']['seeds']})")

    cfg = CalibrationConfig()
    result = run_analysis(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, str(args.cache))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    h = result["arms"]["hard_ce"]
    print(f"\nhard_ce(n={result['headline_n']}): conf={h['conf'][0]:.3f} acc={h['acc'][0]:.3f} "
          f"ECE={h['ece'][0]:.3f} --T={h['T'][0]:.2f}--> ECE={h['ece_T'][0]:.3f} | KL {h['kl'][0]:.3f}->{h['kl_T'][0]:.3f}")
    print("sweep T: " + ", ".join(f"n={n}:{result['sweep'][n]['T'][0]:.2f}" for n in sorted(result['sweep'])))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
