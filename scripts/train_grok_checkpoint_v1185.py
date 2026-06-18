"""v1185: train and save the canonical grokking checkpoint, then demo it.

Trains the frozen default grokking recipe (`a + b = c (mod 97)`, 1-layer MiniGPT,
AdamW lr=1e-3 wd=1.0, train_frac=0.2) once to grok, saves a self-contained
checkpoint, RELOADS it, verifies the reload is bit-identical, and proves
generalization on held-out pairs via the reloaded model.

Example:
    python scripts/train_grok_checkpoint_v1185.py --device cuda
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.grok_checkpoint_v1185 import (  # noqa: E402
    CANONICAL_CONFIG,
    build_report,
    evaluate_generalization,
    load_checkpoint,
    logits_match,
    save_checkpoint,
    train_to_grok,
)
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device  # noqa: E402

STEM = "grok_checkpoint_v1185"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and save the canonical grokking checkpoint.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "grok-checkpoint-v1185")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--max-steps", type=int, default=None, help="override the recipe budget (debug only)")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    device = choose_device(args.device)

    config = CANONICAL_CONFIG
    if args.max_steps is not None:
        from dataclasses import replace

        config = replace(config, max_steps=args.max_steps)

    print(f"device={device} recipe: a+b mod {config.p}, wd={config.wds[0]}, train_frac={config.train_frac}, seed={config.seeds[0]}")

    model, meta, curve = train_to_grok(config, device)
    print(f"trained: memorize_step={meta.t_mem} generalize_step={meta.t_gen} "
          f"final_train_acc={meta.final_train_acc} final_val_acc={meta.final_val_acc}")

    ckpt_path = args.out_dir / f"{STEM}.pt"
    save_checkpoint(model, meta, ckpt_path)

    # reload the saved checkpoint and prove it is bit-identical + generalizes
    reloaded, reloaded_meta = load_checkpoint(ckpt_path, device=device)
    roundtrip_ok = logits_match(model, reloaded, meta.p)
    demo = evaluate_generalization(reloaded, reloaded_meta, device)
    print(f"checkpoint saved -> {ckpt_path}  (roundtrip_logits_identical={roundtrip_ok})")
    print(f"held-out generalization (reloaded model): acc={demo['heldout_acc']} over {demo['n_heldout']} unseen pairs")
    for s in demo["samples"][:6]:
        mark = "OK" if s["correct"] else "X"
        print(f"  [{mark}] {s['a']} + {s['b']} = {s['predicted']} (truth {s['truth']}) mod {meta.p}")

    report = build_report(meta, curve, demo, roundtrip_ok)
    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
