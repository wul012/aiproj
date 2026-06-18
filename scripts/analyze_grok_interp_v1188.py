"""v1188: mechanistic interpretability of the grokked modular-addition model.

For each seed, trains a grokked (wd=1) and a paired memorized-not-grokked (wd=0)
model, builds a random-init null, and compares the Fourier concentration of their
number embeddings. Also reports the shipped v1185 checkpoint's structure.

Example:
    python scripts/analyze_grok_interp_v1188.py --device cuda --seeds 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_interp_v1188 import (  # noqa: E402
    analyze_shipped_checkpoint,
    build_report,
    collect_arms,
    decide,
)
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402

STEM = "grok_interp_v1188"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mechanistic interpretability of the grokked model.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "grok-interp-v1188")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--p", type=int, default=97)
    parser.add_argument("--train-frac", type=float, default=0.2)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--memorize-steps", type=int, default=5000)
    parser.add_argument("--grok-max-steps", type=int, default=40000)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    device = choose_device(args.device)
    seed_everything(1337)

    seeds = tuple(1337 + i for i in range(args.seeds))
    print(f"device={device} p={args.p} train_frac={args.train_frac} seeds={seeds}")

    arms = collect_arms(
        p=args.p, seeds=seeds, train_frac=args.train_frac, device=device,
        memorize_steps=args.memorize_steps, grok_max_steps=args.grok_max_steps,
    )
    info = decide(arms)
    shipped = analyze_shipped_checkpoint(args.p, device)
    report = build_report(arms, info, shipped, args.p)

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    if shipped:
        print(f"shipped v1185 checkpoint: top_k_fraction={shipped['top_k_fraction']} dominant_freq={shipped['dominant_freq']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
