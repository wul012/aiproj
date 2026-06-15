"""v1169: reward modeling + best-of-N. Train a Bradley-Terry reward model on
confusable preference pairs, measure in-distribution vs off-distribution
(random-corruption) ranking accuracy, then rerank a weak base's own samples
(best-of-N) against random-pick and oracle baselines.

Example:
    python scripts/run_reward_model_v1169.py --device cuda --seeds 3
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dpo_preference_v1166 import build_confusable_preferences  # noqa: E402
from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.reward_model_v1169 import RewardModelConfig, run_reward_model  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.script_setup import setup_single_corpus  # noqa: E402
from minigpt.sft_corpus import EOS, INPUT_ALPHABET  # noqa: E402

STEM = "reward_model_v1169"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reward modeling + best-of-N reranking.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "reward-model-v1169")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--corpus-seed", type=int, default=1337)
    parser.add_argument("--ops", type=str, nargs="+", default=["C", "R", "S", "L"])
    parser.add_argument("--lengths", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--inputs-per-op-length", type=int, default=200)
    parser.add_argument("--heldout-ratio", type=float, default=0.25)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--rm-steps", type=int, default=600)
    parser.add_argument("--base-steps", type=int, default=400)
    parser.add_argument("--n-values", type=int, nargs="+", default=[1, 4, 8, 16])
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.corpus_seed)
    device = choose_device(args.device)

    ops = tuple(args.ops)
    corpus, tokenizer, pad_id, eos_id, block_size = setup_single_corpus(
        seed=args.corpus_seed, ops=ops, lengths=tuple(args.lengths),
        inputs_per_op_length=args.inputs_per_op_length, heldout_ratio=args.heldout_ratio)
    tr_pairs, _ = build_confusable_preferences(corpus.train, ops)
    ev_pairs, _ = build_confusable_preferences(corpus.heldout, ops)

    rm_train_pairs = [(tokenizer.encode(p.chosen_text), tokenizer.encode(p.rejected_text)) for p in tr_pairs]
    rm_eval_pairs = [(tokenizer.encode(p.chosen_text), tokenizer.encode(p.rejected_text)) for p in ev_pairs]

    # OFF-DISTRIBUTION rejects: a random corruption of the SAME held-out chosen prompt
    rng = random.Random(args.corpus_seed + 99)
    rm_ood_pairs = []
    for e in corpus.heldout:
        inp = e.prompt[1:-1]
        corrupted = e.expected_output
        while corrupted == e.expected_output:
            corrupted = "".join(rng.choice(INPUT_ALPHABET) for _ in inp)
        rm_ood_pairs.append((tokenizer.encode(e.text), tokenizer.encode(e.prompt + corrupted + EOS)))

    base_train = [(tokenizer.encode(e.text), len(e.prompt)) for e in corpus.train]
    heldout_instructions = [(tokenizer.encode(e.prompt), tokenizer.encode(e.expected_output), e.op) for e in corpus.heldout]

    corpus_stats = {
        "rm_train_pairs": len(rm_train_pairs),
        "rm_eval_pairs": len(rm_eval_pairs),
        "rm_ood_pairs": len(rm_ood_pairs),
    }
    print(
        f"device={device} vocab={tokenizer.vocab_size} ops={','.join(ops)} "
        f"rm_train={len(rm_train_pairs)} rm_eval={len(rm_eval_pairs)} rm_ood={len(rm_ood_pairs)} "
        f"heldout={len(heldout_instructions)} block_size={block_size}"
    )

    config = RewardModelConfig(
        block_size=block_size, seeds=tuple(1337 + i for i in range(args.seeds)),
        rm_steps=args.rm_steps, base_steps=args.base_steps, n_values=tuple(args.n_values),
        temperature=args.temperature, batch_size=args.batch_size,
        n_layer=args.n_layer, n_head=args.n_head, n_embd=args.n_embd, max_new_tokens=max(args.lengths) + 2,
    )
    report = run_reward_model(
        vocab_size=tokenizer.vocab_size, rm_train_pairs=rm_train_pairs, rm_eval_pairs=rm_eval_pairs,
        rm_ood_pairs=rm_ood_pairs, base_train=base_train, heldout_instructions=heldout_instructions,
        ops=ops, pad_id=pad_id, eos_id=eos_id, config=config, device=device, corpus_stats=corpus_stats,
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("best_of_n_curves=" + json.dumps(report.get("best_of_n_curves", {})))
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
