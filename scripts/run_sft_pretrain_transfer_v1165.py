"""v1165: base->SFT transfer. Pretrain a base LM on {copy,reverse,sort}, then SFT
on a held-out new op (shift-left), comparing pretrained vs from-scratch across SFT
budgets.

Example:
    python scripts/run_sft_pretrain_transfer_v1165.py --device auto --seeds 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.readability_report_artifacts import render_readability_text, write_readability_outputs  # noqa: E402
from minigpt.script_runtime import choose_device, seed_everything  # noqa: E402
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus  # noqa: E402
from minigpt.sft_pretrain_transfer_v1165 import SftTransferConfig, run_sft_transfer  # noqa: E402
from minigpt.tokenizer import CharTokenizer  # noqa: E402

STEM = "sft_pretrain_transfer_v1165"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="base->SFT transfer to a held-out op.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "sft-pretrain-transfer-v1165")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--corpus-seed", type=int, default=1337)
    parser.add_argument("--base-ops", type=str, nargs="+", default=["C", "R", "S"])
    parser.add_argument("--downstream-op", type=str, default="L")
    parser.add_argument("--lengths", type=int, nargs="+", default=[3, 4, 5])
    parser.add_argument("--inputs-per-op-length", type=int, default=240)
    parser.add_argument("--heldout-ratio", type=float, default=0.25)
    parser.add_argument("--seeds", type=int, default=3, help="number of model-init seeds (1337..)")
    parser.add_argument("--base-steps", type=int, default=1200)
    parser.add_argument("--sft-schedule", type=int, nargs="+", default=[50, 150, 400, 1000])
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--lr", type=float, default=3e-3)
    parser.add_argument("--batch-size", type=int, default=64)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.corpus_seed)
    device = choose_device(args.device)

    base = build_sft_corpus(seed=args.corpus_seed, ops=tuple(args.base_ops), lengths=tuple(args.lengths),
                            inputs_per_op_length=args.inputs_per_op_length, heldout_ratio=args.heldout_ratio)
    downstream = build_sft_corpus(seed=args.corpus_seed + 1, ops=(args.downstream_op,), lengths=tuple(args.lengths),
                                  inputs_per_op_length=args.inputs_per_op_length, heldout_ratio=args.heldout_ratio)

    all_text = "".join(e.text for e in base.train + base.heldout + downstream.train + downstream.heldout)
    tokenizer = CharTokenizer.train(all_text + base.alphabet)
    pad_id = tokenizer.encode(PAD)[0]
    eos_id = tokenizer.encode(EOS)[0]

    base_stream = "".join(e.text for e in base.train)  # full-LM pretraining stream over {C,R,S}
    base_train_ids = torch.tensor(tokenizer.encode(base_stream), dtype=torch.long)
    downstream_train = [(tokenizer.encode(e.text), len(e.prompt)) for e in downstream.train]
    downstream_heldout = [(tokenizer.encode(e.prompt), tokenizer.encode(e.expected_output), e.op) for e in downstream.heldout]

    block_size = max(16, base.max_text_len, downstream.max_text_len)
    corpus_stats = {
        "base_ops": ",".join(args.base_ops),
        "base_train_char_count": len(base_stream),
        "downstream_train_count": len(downstream_train),
        "downstream_heldout_count": len(downstream_heldout),
    }
    print(
        f"device={device} vocab={tokenizer.vocab_size} base_chars={len(base_stream)} "
        f"downstream_train={len(downstream_train)} downstream_heldout={len(downstream_heldout)} block_size={block_size}"
    )

    config = SftTransferConfig(
        block_size=block_size, seeds=tuple(1337 + i for i in range(args.seeds)),
        base_steps=args.base_steps, base_lr=args.lr, base_batch_size=args.batch_size,
        sft_schedule=tuple(args.sft_schedule), sft_lr=args.lr, sft_batch_size=args.batch_size,
        n_layer=args.n_layer, n_head=args.n_head, n_embd=args.n_embd, max_new_tokens=max(args.lengths) + 2,
    )
    report = run_sft_transfer(
        vocab_size=tokenizer.vocab_size, base_train_ids=base_train_ids,
        downstream_train=downstream_train, downstream_heldout=downstream_heldout,
        downstream_op=args.downstream_op, pad_id=pad_id, eos_id=eos_id,
        config=config, device=device, corpus_stats=corpus_stats,
    )

    outputs = write_readability_outputs(report, args.out_dir, stem=STEM)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
