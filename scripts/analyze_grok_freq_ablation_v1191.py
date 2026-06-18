"""v1191: causal frequency ablation on the shipped grokking checkpoint.

Loads the v1185 checkpoint, removes / keeps Fourier frequencies in the (tied)
number-embedding, and re-measures held-out accuracy to test whether the dominant
frequencies are causally necessary / specific / sufficient for a+b mod 97.
CPU in seconds (no training).

Example:
    python scripts/analyze_grok_freq_ablation_v1191.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_checkpoint_v1185 import load_checkpoint  # noqa: E402
from minigpt.grok_freq_ablation_v1191 import build_report, decide, run_ablation  # noqa: E402
from minigpt.grok_predict_v1186 import DEFAULT_CHECKPOINT  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device  # noqa: E402

STEM = "grok_freq_ablation_v1191"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Causal frequency ablation of the grokking checkpoint.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "grok-freq-ablation-v1191")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--random-trials", type=int, default=5)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    device = choose_device(args.device)

    model, meta = load_checkpoint(args.checkpoint, device=device)
    print(f"loaded {args.checkpoint}  (a+b mod {meta.p})")

    result = run_ablation(model, meta, k=args.k, random_trials=args.random_trials)
    info = decide(result)
    report = build_report(result, info, str(args.checkpoint))

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print(
        f"baseline={result['baseline_acc']}  remove_dominant={result['acc_remove_dominant']}  "
        f"remove_random={result['acc_remove_random_mean']}  keep_dominant={result['acc_keep_dominant']}  "
        f"chance={result['chance']}"
    )
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
