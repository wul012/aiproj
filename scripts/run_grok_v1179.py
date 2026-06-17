"""v1179: grokking — delayed generalization on modular arithmetic.

Trains a 1-layer MiniGPT on ``a + b = c (mod p)`` with a fraction of the (a, b)
pairs held out, and measures whether validation accuracy makes the delayed
grokking phase transition long after the train set is memorized. A paired
``weight_decay=0`` ablation tests that weight decay drives the transition.

Example:
    python scripts/run_grok_v1179.py --device cuda --seeds 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_v1179 import GrokConfig, run_grok  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402

STEM = "grok_v1179"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grokking: delayed generalization on modular addition.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "grok-v1179")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--p", type=int, default=97)
    parser.add_argument("--train-frac", type=float, default=0.2)
    parser.add_argument("--n-layer", type=int, default=1)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1.0)
    parser.add_argument("--max-steps", type=int, default=40000)
    parser.add_argument("--eval-every", type=int, default=100)
    parser.add_argument("--seeds", type=int, default=5)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    device = choose_device(args.device)
    seed_everything(1337)

    config = GrokConfig(
        p=args.p, train_frac=args.train_frac, n_layer=args.n_layer, n_embd=args.n_embd,
        lr=args.lr, max_steps=args.max_steps, eval_every=args.eval_every,
        seeds=tuple(1337 + i for i in range(args.seeds)), wds=(args.weight_decay, 0.0),
    )
    print(
        f"device={device} p={config.p} vocab={config.p + 2} train_frac={config.train_frac} "
        f"n_layer={config.n_layer} max_steps={config.max_steps} seeds={len(config.seeds)} "
        f"wds={config.wds}"
    )

    report = run_grok(config=config, device=device)

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
