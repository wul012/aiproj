"""v1192 Phase A: train the calibration arms ONCE and save per-context logits to a cache.

The single training pass for v1192. Everything downstream (temperature fitting, ECE/NLL/
Brier, specificity controls, decide(), the figure) is pure CPU post-processing on the saved
logits (see analyze_calibration_v1192.py) — so verdict/threshold iteration needs NO retrain
(the project's reuse-cached discipline; mirrors v1185 train -> v1186/88/91 analyze).

Arms (all 2L/32 students on the v1173 stochastic Dirichlet task, known P_true):
  hard_ce (n=10, headline) | soft_distill (faithful soft teacher) | label_smooth (eps~mean H)
  | random_init (untrained anchor); a samples/ctx sweep (n=3..300, the "not magic" trend);
  and a separate LOW-entropy task instance (the expected-null boundary).

Example:
    python scripts/run_calibration_v1192.py --device cuda
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.calibration_v1192 import kl_to_true                              # noqa: E402
from minigpt.distill_common import make_distill_model, train_student          # noqa: E402
from minigpt.distill_v1173 import (                                           # noqa: E402
    EOS, PAD, SEP, build_stochastic_task, eps_for_entropy, _sample_examples,
)
from minigpt.script_runtime import choose_device, seed_everything            # noqa: E402
from minigpt.tokenizer import CharTokenizer                                   # noqa: E402

HEADLINE_N = 10
SWEEP_NS = (3, 10, 30, 100, 300)
BLOCK = 8
STUDENT = dict(n_layer=2, n_head=4, n_embd=32)
TEACHER = dict(n_layer=4, n_head=4, n_embd=64)
STUDENT_STEPS = 700
TEACHER_STEPS = 1200
TEACHER_SAMPLES = 400
LR = 3e-3
BATCH = 64


def build_task(k, seed, alpha_lo, alpha_hi):
    P_true, H, ctx_chars, out_chars = build_stochastic_task(k, seed=seed, alpha_lo=alpha_lo, alpha_hi=alpha_hi)
    tok = CharTokenizer.train(ctx_chars + out_chars + SEP + EOS + PAD)
    sep_id = tok.encode(SEP)[0]; pad_id = tok.encode(PAD)[0]
    contexts = [[tok.encode(c)[0], sep_id] for c in ctx_chars]
    out_ids = [tok.encode(c)[0] for c in out_chars]
    return P_true, H, contexts, out_ids, pad_id, tok.vocab_size


@torch.no_grad()
def sub_logits(model, contexts, out_ids, device):
    X = torch.tensor(contexts, dtype=torch.long, device=device)
    z = model(X)[0][:, -1, :]
    return z[:, out_ids].detach().cpu().numpy().astype(np.float32)


def train_hard(P_true, contexts, out_ids, pad_id, vocab, n, seed, device):
    rng = np.random.default_rng(seed)
    ex = _sample_examples(P_true, contexts, out_ids, n, rng)
    torch.manual_seed(seed)
    s = make_distill_model(vocab, BLOCK, **STUDENT).to(device)
    train_student(s, ex, steps=STUDENT_STEPS, lr=LR, batch_size=BATCH, block_size=BLOCK,
                  pad_id=pad_id, device=device, loss_mode="ce")
    return sub_logits(s, contexts, out_ids, device)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="v1192 Phase A: train calibration arms, save logit cache.")
    p.add_argument("--out", type=Path, default=ROOT / "output" / "calibration-v1192" / "cache.pt")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--k-contexts", type=int, default=32)
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--corpus-seed", type=int, default=1337)
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.corpus_seed)
    device = choose_device(args.device)
    seeds = tuple(1337 + i for i in range(args.seeds))

    # ---- main stochastic task (known P_true, entropy swept) ----
    P_true, H, contexts, out_ids, pad_id, vocab = build_task(args.k_contexts, args.corpus_seed, 0.12, 6.0)
    M = len(out_ids); mean_H = float(H.mean())
    uniform_kl_floor = float(np.log(M) - mean_H)
    print(f"device={device} K={args.k_contexts} M={M} vocab={vocab} mean_H={mean_H:.3f} "
          f"spread={float(H.max()-H.min()):.3f} uniform_kl_floor={uniform_kl_floor:.3f}")

    # ---- faithful soft teacher (many samples/ctx, larger model) ----
    rng = np.random.default_rng(10_000 + args.corpus_seed)
    tex = _sample_examples(P_true, contexts, out_ids, TEACHER_SAMPLES, rng)
    torch.manual_seed(args.corpus_seed)
    teacher = make_distill_model(vocab, BLOCK, **TEACHER).to(device)
    train_student(teacher, tex, steps=TEACHER_STEPS, lr=LR, batch_size=BATCH, block_size=BLOCK,
                  pad_id=pad_id, device=device, loss_mode="ce")
    teacher.eval()
    teacher_kl = float(kl_to_true(P_true, sub_logits(teacher, contexts, out_ids, device), 1.0))
    print(f"teacher KL(true||teacher)={teacher_kl:.4f} (faithful if << uniform_kl_floor)")

    eps = eps_for_entropy(mean_H, M)
    ctx_prompts = [list(c) for c in contexts]

    arms = {"hard_ce": {}, "soft_distill": {}, "label_smooth": {}, "random_init": {}}
    sweep = {n: {} for n in SWEEP_NS}
    boundary = {}
    # ---- low-entropy boundary task (peaky P_true -> expected null) ----
    bP, bH, bctx, bout, bpad, bvocab = build_task(args.k_contexts, args.corpus_seed + 7, 0.02, 0.15)
    print(f"boundary task mean_H={float(bH.mean()):.3f} spread={float(bH.max()-bH.min()):.3f} (low-entropy)")

    for seed in seeds:
        # headline hard_ce (n=10)
        z_hard = train_hard(P_true, contexts, out_ids, pad_id, vocab, HEADLINE_N, seed, device)
        arms["hard_ce"][seed] = z_hard

        # soft_distill (distill from teacher0, hard_weight=0; label irrelevant)
        ex = [(c + [out_ids[0]], len(c)) for c in ctx_prompts]
        torch.manual_seed(seed)
        s = make_distill_model(vocab, BLOCK, **STUDENT).to(device)
        train_student(s, ex, steps=STUDENT_STEPS, lr=LR, batch_size=BATCH, block_size=BLOCK,
                      pad_id=pad_id, device=device, loss_mode="distill", teacher=teacher, tau=1.0, hard_weight=0.0)
        arms["soft_distill"][seed] = sub_logits(s, contexts, out_ids, device)

        # label_smooth (n=10, generic flattening control)
        rng2 = np.random.default_rng(seed)
        ex_ls = _sample_examples(P_true, contexts, out_ids, HEADLINE_N, rng2)
        torch.manual_seed(seed)
        s = make_distill_model(vocab, BLOCK, **STUDENT).to(device)
        train_student(s, ex_ls, steps=STUDENT_STEPS, lr=LR, batch_size=BATCH, block_size=BLOCK,
                      pad_id=pad_id, device=device, loss_mode="ce", label_smoothing=eps)
        arms["label_smooth"][seed] = sub_logits(s, contexts, out_ids, device)

        # random_init (untrained anchor)
        torch.manual_seed(seed)
        s = make_distill_model(vocab, BLOCK, **STUDENT).to(device)
        arms["random_init"][seed] = sub_logits(s, contexts, out_ids, device)

        # sweep (reuse headline for n=10)
        for n in SWEEP_NS:
            sweep[n][seed] = z_hard if n == HEADLINE_N else train_hard(
                P_true, contexts, out_ids, pad_id, vocab, n, seed, device)

        # boundary hard_ce (n=10 on the low-entropy task)
        boundary[seed] = train_hard(bP, bctx, bout, bpad, bvocab, HEADLINE_N, seed, device)
        print(f"  seed {seed} done")

    cache = {
        "p_true": P_true, "H": H, "arms": arms, "sweep": sweep,
        "boundary": boundary, "boundary_p_true": bP, "boundary_H": bH,
        "teacher_kl": teacher_kl, "uniform_kl_floor": uniform_kl_floor, "headline_n": HEADLINE_N,
        "meta": {"k": args.k_contexts, "M": M, "vocab": vocab, "seeds": list(seeds),
                 "student": STUDENT, "teacher": TEACHER, "student_steps": STUDENT_STEPS,
                 "label_smoothing_eps": float(eps)},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"saved cache -> {args.out}")


if __name__ == "__main__":
    main()
