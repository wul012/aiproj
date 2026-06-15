"""v1170: speculative decoding — verified-correct, FLOPs-honest.

Trains a target on the {C,R,S,L} SFT corpus (snapshotting under-trained drafts
along the way), then for each (draft, K) measures: correctness (logit-identity +
greedy + sampling-TV + accept-rule consistency = the GATE), graded acceptance
alpha, the FLOPs-honest target_positions metric, and a repeated-trial wall-clock
comparison vs plain cached decoding.

Example:
    python scripts/run_spec_decode_v1170.py --device cuda --seeds 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus  # noqa: E402
from minigpt.spec_decode_v1170 import SpecDecodeConfig, run_spec_decode  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "spec_decode_v1170"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Speculative decoding: verified-correct, FLOPs-honest.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "spec-decode-v1170")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--corpus-seed", type=int, default=1337)
    parser.add_argument("--ops", type=str, nargs="+", default=["C", "R", "S", "L"])
    parser.add_argument("--lengths", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--inputs-per-op-length", type=int, default=160)
    parser.add_argument("--heldout-ratio", type=float, default=0.25)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--target-steps", type=int, default=800)
    parser.add_argument("--draft-snapshot-steps", type=int, nargs="+", default=[30, 80, 200, 450])
    parser.add_argument("--k-values", type=int, nargs="+", default=[1, 2, 4])
    parser.add_argument("--eval-prompts", type=int, default=80)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--tv-repeats", type=int, default=40)
    parser.add_argument("--timing-repeats", type=int, default=12)
    parser.add_argument("--timing-k", type=int, default=4)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=64)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.corpus_seed)
    device = choose_device(args.device)

    ops = tuple(args.ops)
    corpus = build_sft_corpus(seed=args.corpus_seed, ops=ops, lengths=tuple(args.lengths),
                              inputs_per_op_length=args.inputs_per_op_length, heldout_ratio=args.heldout_ratio)
    tokenizer = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
    pad_id = tokenizer.encode(PAD)[0]
    eos_id = tokenizer.encode(EOS)[0]

    base_train = [(tokenizer.encode(e.text), len(e.prompt)) for e in corpus.train]
    heldout_instructions = [(tokenizer.encode(e.prompt), tokenizer.encode(e.expected_output), e.op) for e in corpus.heldout]
    block_size = max(16, corpus.max_text_len)
    max_new_tokens = max(args.lengths) + 2

    print(
        f"device={device} vocab={tokenizer.vocab_size} ops={','.join(ops)} "
        f"train={len(base_train)} heldout={len(heldout_instructions)} block_size={block_size} "
        f"max_new={max_new_tokens} drafts={args.draft_snapshot_steps} k={args.k_values}"
    )

    config = SpecDecodeConfig(
        block_size=block_size,
        seeds=tuple(1337 + i for i in range(args.seeds)),
        target_steps=args.target_steps,
        draft_snapshot_steps=tuple(args.draft_snapshot_steps),
        k_values=tuple(args.k_values),
        max_new_tokens=max_new_tokens,
        eval_prompts=args.eval_prompts,
        temperature=args.temperature,
        tv_repeats=args.tv_repeats,
        timing_repeats=args.timing_repeats,
        timing_k=args.timing_k,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd,
    )
    report = run_spec_decode(
        vocab_size=tokenizer.vocab_size, base_train=base_train, heldout_instructions=heldout_instructions,
        ops=ops, pad_id=pad_id, eos_id=eos_id, config=config, device=device,
        corpus_stats={"heldout_prompts": len(heldout_instructions)},
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("alpha_by_draft_k=" + json.dumps(report.get("alpha_by_draft_k", {})))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
