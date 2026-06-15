"""v1172: knowledge distillation — label transfer, not dark knowledge.

Trains a teacher on {C,R,S,L}, then distills it into a student-size sweep and
compares KL-distillation to hard-label SFT with two disentangling controls
(label-smoothing matched to the teacher's confidence; a shuffled-teacher that
preserves argmax+entropy but destroys class identity) plus a matched-FLOPs
scratch baseline. The pre-registered contrast is distill_tau1_hw0 vs scratch_hard
and both controls, at the capable student.

Example:
    python scripts/run_distill_v1172.py --device cuda --seeds 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.distill_v1172 import DistillConfig, run_distill  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.script_setup import setup_single_corpus  # noqa: E402

STEM = "distill_v1172"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Knowledge distillation: label transfer vs dark knowledge.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "distill-v1172")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--corpus-seed", type=int, default=1337)
    parser.add_argument("--ops", type=str, nargs="+", default=["C", "R", "S", "L"])
    parser.add_argument("--lengths", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--inputs-per-op-length", type=int, default=120)
    parser.add_argument("--heldout-ratio", type=float, default=0.25)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--teacher-steps", type=int, default=800)
    parser.add_argument("--steps", type=int, default=700)
    parser.add_argument("--train-fit-prompts", type=int, default=120)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.corpus_seed)
    device = choose_device(args.device)

    ops = tuple(args.ops)
    corpus, tokenizer, pad_id, eos_id, block_size = setup_single_corpus(
        seed=args.corpus_seed, ops=ops, lengths=tuple(args.lengths),
        inputs_per_op_length=args.inputs_per_op_length, heldout_ratio=args.heldout_ratio)

    train_examples = [(tokenizer.encode(e.text), len(e.prompt)) for e in corpus.train]
    heldout_instructions = [(tokenizer.encode(e.prompt), tokenizer.encode(e.expected_output), e.op) for e in corpus.heldout]
    train_instructions = [(tokenizer.encode(e.prompt), tokenizer.encode(e.expected_output), e.op)
                          for e in corpus.train[: args.train_fit_prompts]]

    print(
        f"device={device} vocab={tokenizer.vocab_size} ops={','.join(ops)} "
        f"train={len(train_examples)} heldout={len(heldout_instructions)} block_size={block_size}"
    )

    config = DistillConfig(
        block_size=block_size, seeds=tuple(1337 + i for i in range(args.seeds)), seed_base=1337,
        teacher_steps=args.teacher_steps, steps=args.steps,
    )
    report = run_distill(
        vocab_size=tokenizer.vocab_size, train_examples=train_examples,
        heldout_instructions=heldout_instructions, train_instructions=train_instructions,
        ops=ops, pad_id=pad_id, eos_id=eos_id, config=config, device=device,
        corpus_stats={"heldout_prompts": len(heldout_instructions)},
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("capacity_curve=" + json.dumps(report.get("capacity_curve", {})))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
