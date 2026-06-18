"""v1186: load and USE the canonical grokking checkpoint.

Loads the shipped v1185 checkpoint, re-derives its train/held-out accuracy
independently, decodes a few demo problems, and (optionally) answers specific
`a b` pairs from the command line. CPU is fine.

Examples:
    python scripts/use_grok_checkpoint_v1186.py
    python scripts/use_grok_checkpoint_v1186.py --pairs 36 37 4 1 50 50
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_predict_v1186 import (  # noqa: E402
    DEFAULT_CHECKPOINT,
    DEMO_PAIRS,
    build_report,
    evaluate_table,
    predict_pairs,
)
from minigpt.grok_checkpoint_v1185 import load_checkpoint  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device  # noqa: E402

STEM = "grok_predict_v1186"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Use the canonical grokking checkpoint.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "grok-predict-v1186")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--pairs", type=int, nargs="+", default=None,
                        help="flat list of a b a b ... to answer (e.g. --pairs 36 37 4 1)")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    device = choose_device(args.device)

    model, meta = load_checkpoint(args.checkpoint, device=device)
    print(f"loaded {args.checkpoint}  (a+b mod {meta.p}, wd={meta.weight_decay}, seed={meta.seed})")

    table = evaluate_table(model, meta)
    print(f"re-derived from checkpoint: train_acc={table['train_acc']} "
          f"heldout_acc={table['heldout_acc']} over {table['n_heldout']} unseen pairs")

    pairs = DEMO_PAIRS
    if args.pairs:
        flat = args.pairs
        if len(flat) % 2 != 0:
            raise SystemExit("--pairs needs an even count: a b a b ...")
        pairs = [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
    demo_rows = predict_pairs(model, pairs, meta.p)
    for r in demo_rows:
        mark = "OK" if r["correct"] else "X"
        print(f"  [{mark}] {r['a']} + {r['b']} = {r['predicted']} (truth {r['truth']}) mod {meta.p}")

    report = build_report(meta, table, demo_rows, str(args.checkpoint))
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
