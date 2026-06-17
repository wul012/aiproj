"""v1183: weight-decay dose-response for grokking.

Sweeps weight-decay strength on `a + b = c (mod 97)` (grokking regime,
train_frac=0.2) and measures how the generalization step depends on it — turning
v1179's binary "weight decay drives grokking" into a dose-response. Reuses the
v1179 per-arm training primitive; paired init+split per seed across all wd arms.

Example:
    python scripts/run_grok_wd_law_v1183.py --device cuda --seeds 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_wd_law_v1183 import DEFAULT_WDS, WdLawConfig, run_wd_law  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402

STEM = "grok_wd_law_v1183"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grokking weight-decay dose-response.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "grok-wd-law-v1183")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--p", type=int, default=97)
    parser.add_argument("--train-frac", type=float, default=0.2)
    parser.add_argument("--max-steps", type=int, default=40000)
    parser.add_argument("--eval-every", type=int, default=200)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--wds", type=float, nargs="+", default=list(DEFAULT_WDS))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    device = choose_device(args.device)
    seed_everything(1337)

    config = WdLawConfig(
        p=args.p, train_frac=args.train_frac, max_steps=args.max_steps, eval_every=args.eval_every,
        seeds=tuple(1337 + i for i in range(args.seeds)), wds=tuple(args.wds),
    )
    print(
        f"device={device} p={config.p} train_frac={config.train_frac} "
        f"max_steps={config.max_steps} seeds={len(config.seeds)} wds={config.wds}"
    )

    report = run_wd_law(config=config, device=device)

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
