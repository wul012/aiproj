"""v1168: NLL-regularized DPO (DPO+SFT-aux). From a weak SFT init, sweep λ in
L = L_DPO + λ·SFT_CE_mean(chosen) and measure whether the aux recovers the
generation vanilla DPO destroys, and whether it does anything plain SFT-on-chosen
does not, against the λ=0 (vanilla DPO) and SFT-on-chosen endpoints.

Example:
    python scripts/run_dpo_sft_aux_v1168.py --device cuda --seeds 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dpo_preference_v1166 import build_confusable_preferences  # noqa: E402
from minigpt.dpo_sft_aux_v1168 import DpoSftAuxConfig, run_dpo_sft_aux  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.script_setup import setup_single_corpus  # noqa: E402

STEM = "dpo_sft_aux_v1168"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NLL-regularized DPO (DPO+SFT-aux) λ sweep.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "dpo-sft-aux-v1168")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--corpus-seed", type=int, default=1337)
    parser.add_argument("--ops", type=str, nargs="+", default=["C", "R", "S", "L"])
    parser.add_argument("--lengths", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--inputs-per-op-length", type=int, default=200)
    parser.add_argument("--heldout-ratio", type=float, default=0.25)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--sft-init-steps", type=int, default=3000)
    parser.add_argument("--budget", type=int, default=1600, help="forward-pass budget (dpo=budget//2 steps, sft=budget)")
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--lambda-grid", type=float, nargs="+", default=[0.0, 0.25, 0.5, 1.0, 2.0, 5.0])
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--gate-lower", type=float, default=0.40)
    parser.add_argument("--gate-upper", type=float, default=0.85)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.corpus_seed)
    device = choose_device(args.device)

    ops = tuple(args.ops)
    corpus, tokenizer, pad_id, eos_id, block_size = setup_single_corpus(
        seed=args.corpus_seed, ops=ops, lengths=tuple(args.lengths),
        inputs_per_op_length=args.inputs_per_op_length, heldout_ratio=args.heldout_ratio)
    train_pairs, dropped_train = build_confusable_preferences(corpus.train, ops)
    eval_pairs, dropped_eval = build_confusable_preferences(corpus.heldout, ops)

    def triple(pair):
        return (tokenizer.encode(pair.chosen_text), pair.n_prompt, tokenizer.encode(pair.rejected_text), pair.n_prompt)

    pref_train_triples = [triple(p) for p in train_pairs]
    eval_triples = [triple(p) for p in eval_pairs]
    eval_heldout_instructions = [(tokenizer.encode(e.prompt), tokenizer.encode(e.expected_output), e.op) for e in corpus.heldout]
    eval_confusable = [
        (tokenizer.encode(p.prompt), tokenizer.encode(p.chosen_output), tokenizer.encode(p.rejected_output), p.op)
        for p in eval_pairs
    ]
    sft_init_train = [(tokenizer.encode(e.text), len(e.prompt)) for e in corpus.train]

    corpus_stats = {
        "pref_train_pairs": len(pref_train_triples),
        "pref_eval_pairs": len(eval_triples),
        "dropped_degenerate_pairs": dropped_train + dropped_eval,
    }
    print(
        f"device={device} vocab={tokenizer.vocab_size} ops={','.join(ops)} "
        f"pref_train={len(pref_train_triples)} pref_eval={len(eval_triples)} block_size={block_size} "
        f"lambda_grid={args.lambda_grid}"
    )

    config = DpoSftAuxConfig(
        block_size=block_size, seeds=tuple(1337 + i for i in range(args.seeds)),
        sft_init_steps=args.sft_init_steps, budget=args.budget, beta=args.beta, lr=args.lr,
        lambda_grid=tuple(args.lambda_grid), batch_size=args.batch_size,
        n_layer=args.n_layer, n_head=args.n_head, n_embd=args.n_embd,
        max_new_tokens=max(args.lengths) + 2, gate_lower=args.gate_lower, gate_upper=args.gate_upper,
    )
    report = run_dpo_sft_aux(
        vocab_size=tokenizer.vocab_size, sft_init_train=sft_init_train,
        pref_train_triples=pref_train_triples, eval_triples=eval_triples,
        eval_heldout_instructions=eval_heldout_instructions, eval_confusable=eval_confusable,
        ops=ops, pad_id=pad_id, eos_id=eos_id, config=config, device=device, corpus_stats=corpus_stats,
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("exact_match_by_lambda=" + json.dumps(report.get("exact_match_by_lambda", {})))
    print("confusable_by_lambda=" + json.dumps(report.get("confusable_by_lambda", {})))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
