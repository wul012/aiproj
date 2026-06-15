"""v1173: distillation under aleatoric uncertainty — dark knowledge made real.

Builds a stochastic Dirichlet task (known P_true per context, entropy swept), trains
a soft teacher, and compares hard-label vs soft distillation on the exact metric
KL(P_true || P_student), isolating dark knowledge (soft vs teacher-argmax) from
data-efficiency (a sample-count sweep) and generic smoothing (label_smooth control).

Example:
    python scripts/run_distill_v1173.py --device cuda --seeds 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.distill_v1173 import (  # noqa: E402
    EOS, PAD, SEP, DistillUncertaintyConfig, build_stochastic_task, run_distill_uncertainty,
)
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "distill_v1173"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Distillation under aleatoric uncertainty (dark knowledge made real).")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "distill-v1173")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--corpus-seed", type=int, default=1337)
    parser.add_argument("--k-contexts", type=int, default=32)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--teacher-steps", type=int, default=1200)
    parser.add_argument("--student-steps", type=int, default=700)
    parser.add_argument("--student-samples", type=int, default=1)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.corpus_seed)
    device = choose_device(args.device)

    P_true, H, ctx_chars, out_chars = build_stochastic_task(args.k_contexts, seed=args.corpus_seed)
    tokenizer = CharTokenizer.train(ctx_chars + out_chars + SEP + EOS + PAD)
    sep_id = tokenizer.encode(SEP)[0]
    pad_id = tokenizer.encode(PAD)[0]
    contexts = [[tokenizer.encode(c)[0], sep_id] for c in ctx_chars]
    out_ids = [tokenizer.encode(c)[0] for c in out_chars]

    print(
        f"device={device} vocab={tokenizer.vocab_size} K={len(contexts)} M={len(out_ids)} "
        f"mean_H={float(H.mean()):.3f} nats spread={float(H.max()-H.min()):.3f}"
    )

    config = DistillUncertaintyConfig(
        seeds=tuple(1337 + i for i in range(args.seeds)), seed_base=1337,
        k_contexts=args.k_contexts, teacher_steps=args.teacher_steps,
        student_steps=args.student_steps, student_samples_per_ctx=args.student_samples,
    )
    report = run_distill_uncertainty(
        vocab_size=tokenizer.vocab_size, P_true=P_true, H=H, contexts=contexts, out_ids=out_ids,
        pad_id=pad_id, config=config, device=device,
        corpus_stats={"heldout_prompts": len(contexts)},
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("scratch_many_kl=" + json.dumps(report.get("scratch_many_kl", {})))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
