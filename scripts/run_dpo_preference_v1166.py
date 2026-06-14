"""v1166: DPO-lite preference tuning. From a deliberately-weak SFT init, optimize
the DPO loss on (prompt, chosen, confusable-rejected) triples and measure the
honest divergence between the optimization target (preference accuracy, rises)
and the capability metric (held-out exact-match, can regress), against a
matched-compute SFT-on-chosen control and a no-reference ablation.

Example:
    python scripts/run_dpo_preference_v1166.py --device auto --seeds 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dpo_preference_v1166 import (  # noqa: E402
    DpoPreferenceConfig,
    build_confusable_preferences,
    run_dpo_preference,
)
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "dpo_preference_v1166"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DPO-lite preference tuning vs SFT-on-chosen control.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "dpo-preference-v1166")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--corpus-seed", type=int, default=1337)
    parser.add_argument("--ops", type=str, nargs="+", default=["C", "R", "S", "L"])
    parser.add_argument("--lengths", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--inputs-per-op-length", type=int, default=200)
    parser.add_argument("--heldout-ratio", type=float, default=0.25)
    parser.add_argument("--seeds", type=int, default=3, help="number of model-init seeds (1337..)")
    parser.add_argument("--sft-init-steps", type=int, default=3000, help="weak SFT init; calibrated to land all-seed exact-match in the headroom band")
    parser.add_argument("--budget-sweep", type=int, nargs="+", default=[240, 720, 1600], help="FORWARD-pass budgets")
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--lr", type=float, default=1e-3)
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
    corpus = build_sft_corpus(seed=args.corpus_seed, ops=ops, lengths=tuple(args.lengths),
                              inputs_per_op_length=args.inputs_per_op_length, heldout_ratio=args.heldout_ratio)

    train_pairs, dropped_train = build_confusable_preferences(corpus.train, ops)
    eval_pairs, dropped_eval = build_confusable_preferences(corpus.heldout, ops)

    tokenizer = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
    pad_id = tokenizer.encode(PAD)[0]
    eos_id = tokenizer.encode(EOS)[0]

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

    block_size = max(16, corpus.max_text_len)
    corpus_stats = {
        "pref_train_pairs": len(pref_train_triples),
        "pref_eval_pairs": len(eval_triples),
        "dropped_degenerate_pairs": dropped_train + dropped_eval,
    }
    print(
        f"device={device} vocab={tokenizer.vocab_size} ops={','.join(ops)} "
        f"pref_train={len(pref_train_triples)} pref_eval={len(eval_triples)} "
        f"dropped_degenerate={dropped_train + dropped_eval} block_size={block_size}"
    )

    config = DpoPreferenceConfig(
        block_size=block_size, seeds=tuple(1337 + i for i in range(args.seeds)),
        sft_init_steps=args.sft_init_steps, budget_sweep=tuple(args.budget_sweep),
        beta=args.beta, lr=args.lr, batch_size=args.batch_size,
        n_layer=args.n_layer, n_head=args.n_head, n_embd=args.n_embd,
        max_new_tokens=max(args.lengths) + 2, gate_lower=args.gate_lower, gate_upper=args.gate_upper,
    )
    report = run_dpo_preference(
        vocab_size=tokenizer.vocab_size, sft_init_train=sft_init_train,
        pref_train_triples=pref_train_triples, eval_triples=eval_triples,
        eval_heldout_instructions=eval_heldout_instructions, eval_confusable=eval_confusable,
        ops=ops, pad_id=pad_id, eos_id=eos_id, config=config, device=device, corpus_stats=corpus_stats,
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("scaling_grid=" + json.dumps(report.get("scaling_grid_rows", []), ensure_ascii=True))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
