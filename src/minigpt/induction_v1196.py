"""v1196: IN-CONTEXT INDUCTION REQUIRES DEPTH -- once you block the shortcuts (a fresh axis).

After the continual-learning arc (v1193-95), a clean pivot to the canonical transformer
phenomenon: INDUCTION (in-context copying), the mechanism behind in-context learning. Toy
scale is its native habitat (induction heads were found in 2-layer attention-only models).

The honest result, found by 5 CPU probes that each FALSIFIED a naive framing:

* concat(S,S) (a fixed-offset exact repeat) is solved by a 1-LAYER POSITIONAL copy ("look back
  L"), NOT induction -> a positional shortcut.
* a free-running forced-successor walk COLLAPSES into short cycles (~6 distinct tokens of 20),
  so an in-context UNIGRAM/frequency heuristic counterfeits induction and even a 1-layer model
  (and a random-init model) score on it.
* On a CLEAN task that blocks BOTH shortcuts -- a high-diversity random sequence whose induction
  target is "the token that most-recently followed the current token" (variable distance, target
  uncorrelated with frequency) -- a 1-LAYER transformer (even with its MLP, across a wide width
  sweep) CANNOT learn induction, while a 2-LAYER model learns it at modest width.

So induction GENUINELY REQUIRES DEPTH; the naive tasks merely let shallow models fake it. We
demonstrate the requirement on the clean task AND show, as a control, that the SAME 1-layer model
DOES succeed on the fixed-offset (positional) task -- so its clean-task failure is a content-
induction limitation, not a general incapacity.

TASK (clean induction). Input = a uniform random length-T sequence over K tokens (~all K appear,
no cycles). At position i the target is x[j+1] where j is the MOST RECENT earlier occurrence of
x[i] (predictable only by content-matching at a variable distance); first occurrences are MASKED
out of the loss (ignore_index). The headline metric is inductable accuracy (acc on unmasked
positions); chance is 1/K and the in-context UNIGRAM heuristic floor is measured analytically.

QUESTION (pre-registered): does induction require DEPTH? For each depth d in {1,2} define the
width-threshold W*_d = the smallest model width whose mean inductable accuracy crosses a success
bar S; the textbook predicts W*_1 = infinity (1 layer never succeeds) while W*_2 is finite. We
sweep width widely (up to ~16x the 2-layer threshold) to bound the claim.

Hardened by a 4-lens adversarial design panel. The non-obvious decisions it forced:

* UNIGRAM gate: gate ``inductable_acc >> unigram_acc`` (analytic, model-free), not ``> chance``.
* SWAP causal probe: change the in-context successor; a true inductor's prediction FOLLOWS it
  (a frequency/recency heuristic does not).
* SHORTCUT control: the same 1-layer model on the fixed-offset (positional) task must SUCCEED --
  else "1-layer fails" could just mean "1-layer learns nothing".
* ATTENTION-ONLY arm (MLP zeroed): the textbook theorem is attention-only; this MiniGPT has an
  MLP in every block, so we test whether the MLP is what (if anything) a shallow model leans on,
  and whether a 2-layer ATTENTION-ONLY model already inducts. We do NOT claim to refute the
  attention-only theorem; we report consistency with it.
* W*-ORDERING (not per-width gap hunting): pre-registered success bar S, W* by interpolation,
  >=5 seeds, std==0 guards, random-init ICL ~ 0 gate.
* induction-attention metric = mass an inductable query places on the MOST-RECENT successor
  position (the one that defines the target), summed over heads, minus the uniform baseline; plus
  a layer-0 prev-token score -- the textbook composed circuit, measured correctly.

``status=="pass"`` certifies a VALID measurement (clean task genuinely in-context past the
unigram floor; 2-layer succeeds so the task is learnable; the 1-layer shortcut-control succeeds
so a clean-task 1-layer failure is meaningful), NEVER a flattering shape. Phase A trains +
caches; Phase B is CPU-only and re-derives the verdict with zero retrain.

Scope: toy synthetic induction, 1-2 layer MiniGPT WITH MLP + learned absolute positions, tied
embeddings, fixed budget, single (K,T); a within-swept-width statement, not a claim about LLM
in-context learning.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn as nn

from minigpt.experiment_utils import mean_std
from minigpt.induction_v1196_decision import (
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    decide_induction,
)
from minigpt.induction_v1196_report import build_induction_report
from minigpt.model import GPTConfig, MiniGPT

IGNORE = -100   # ignore_index used by F.cross_entropy in MiniGPT.forward


@dataclass
class InductionConfig:
    # --- task (pinned before seeing cached results) ---
    K: int = 20                     # vocab size
    T: int = 64                     # sequence length
    widths: tuple[int, ...] = (8, 16, 24, 32, 48, 64, 96, 128)
    depths: tuple[int, ...] = (1, 2)
    shortcut_widths: tuple[int, ...] = (16, 32, 64)        # 1-layer on the positional task (capability control)
    attn_only_widths: tuple[int, ...] = (24, 48, 96)       # MLP-zeroed arms (textbook-regime control)
    n_head: int = 4
    lr: float = 1e-3
    beta1: float = 0.9
    beta2: float = 0.98
    weight_decay: float = 0.1
    dropout: float = 0.0
    steps: int = 1500
    batch: int = 256
    eval_every: int = 50            # inductable-acc trajectory cadence
    eval_batch: int = 256
    eval_n_batches: int = 6
    mech_batch: int = 64
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341)
    # --- decide() thresholds (pinned) ---
    s_success_frac: float = 0.6     # success bar S = s_success_frac * ceiling
    verdict_max_width: int = 64     # depth verdict uses the width range where 2-layer training
                                    # converges; larger widths under-train at the fixed step budget
                                    # (an optimization effect) and are reported, not used in gates.
    unigram_margin: float = 0.15    # inductable acc must beat the in-context unigram acc by this
    min_gap_margin: float = 0.05    # margin for "A beats B" (guards std==0)
    gap_closed_eps: float = 0.05    # equivalence band when asking if 1L caught up at the widest width
    paired_frac: float = 0.8        # fraction of seeds for a paired ordering claim
    random_init_acc_max: float = 0.15   # untrained model inductable acc must be <= this
    swap_follow_min: float = 0.5    # a genuine inductor's swap-follow rate (reported)

    @property
    def chance(self) -> float:
        return 1.0 / self.K

    @property
    def ceiling(self) -> float:
        return 1.0 - 1.0 / self.K

    @property
    def S(self) -> float:
        return self.s_success_frac * self.ceiling


# ------------------------------------------------------------------------- task generation
def make_batch(cfg: InductionConfig, bsz: int, gen: torch.Generator, device,
               mode: str = "clean") -> tuple[torch.Tensor, torch.Tensor]:
    """Returns (x, target) of shapes (bsz, T) and (bsz, T-1); target uses IGNORE on masked positions.

    mode="clean": x is a uniform random sequence; target[i] = x[j+1], j = most recent earlier
      occurrence of x[i] (induction at variable distance); first occurrences are masked. (Vectorized
      over the batch; loop only over T positions.)
    mode="fixed_offset": x = concat(S, S) for random S of length T/2 (a positional shortcut control);
      target = next token, with the first copy masked so only the (positionally copyable) second
      copy is scored.
    """
    K, T = cfg.K, cfg.T
    if mode == "clean":
        x = torch.randint(0, K, (bsz, T), generator=gen, device=device)
        # target[i] = x[j+1], j = MOST RECENT earlier occurrence of x[i]; first occurrences masked.
        # Fully vectorized (one (B,T,T) op) -- NO per-position Python loop / kernel-launch storm.
        eq = (x.unsqueeze(2) == x.unsqueeze(1))                       # (B,T,T): eq[b,i,j] = x[b,i]==x[b,j]
        earlier = torch.tril(torch.ones(T, T, dtype=torch.bool, device=device), diagonal=-1)  # j < i
        eq = eq & earlier
        has = eq.any(dim=2)                                            # (B,T) any earlier occurrence
        jpos = (eq * torch.arange(T, device=device)).argmax(dim=2)     # (B,T) most-recent earlier j
        src = (jpos + 1).clamp(max=T - 1)
        succ = torch.gather(x, 1, src)                                 # (B,T) x[j+1]
        target = torch.where(has, succ, torch.full_like(succ, IGNORE))[:, : T - 1].contiguous()
        return x, target
    if mode == "fixed_offset":
        L = T // 2
        S = torch.randint(0, K, (bsz, L), generator=gen, device=device)
        x = torch.cat([S, S], dim=1)
        target = x[:, 1:].clone()
        target[:, : L - 1] = IGNORE          # only the second-copy predictions are inductable
        return x, target
    raise ValueError(f"unknown mode {mode!r}")


def unigram_acc(cfg: InductionConfig, x: torch.Tensor, target: torch.Tensor) -> tuple[float, float]:
    """Analytic, model-free in-context unigram predictor: at position i predict argmax of token
    counts strictly before i. Returns (inductable_acc, max_marginal) over unmasked positions."""
    B, T = x.shape
    K = cfg.K
    c = n = 0
    marg_sum = marg_cnt = 0.0
    for b in range(B):
        counts = torch.zeros(K, dtype=torch.long)
        for i in range(T - 1):
            if i > 0 and int(target[b, i]) != IGNORE:
                pred = int(counts.argmax())
                marg_sum += counts.max().item() / i; marg_cnt += 1
                c += int(pred == int(target[b, i])); n += 1
            counts[int(x[b, i])] += 1
    return c / max(n, 1), marg_sum / max(marg_cnt, 1)


# ------------------------------------------------------------------------- model + training
class _ZeroMLP(nn.Module):
    """Drop-in replacement making a Block attention-only (MLP contributes nothing)."""
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.zeros_like(x)


def make_model(cfg: InductionConfig, depth: int, width: int, attn_only: bool, seed: int) -> MiniGPT:
    torch.manual_seed(seed)
    model = MiniGPT(GPTConfig(vocab_size=cfg.K, block_size=cfg.T, n_layer=depth, n_head=cfg.n_head,
                              n_embd=width, dropout=cfg.dropout, use_rope=False))
    if attn_only:
        for blk in model.blocks:
            blk.mlp = _ZeroMLP()
    return model


def _inductable_acc(model: MiniGPT, eval_x, eval_t, device) -> float:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, t in zip(eval_x, eval_t):
            x = x.to(device); t = t.to(device)
            pred = model(x[:, :-1])[0].argmax(-1)
            m = t != IGNORE
            correct += (pred[m] == t[m]).sum().item(); total += int(m.sum())
    return correct / max(total, 1)


def _swap_follow(cfg: InductionConfig, model: MiniGPT, x: torch.Tensor, t: torch.Tensor, device,
                 seed: int) -> float:
    """Causal probe: for each row take the LAST inductable query i (current token c, most-recent
    earlier occurrence j defines target x[j+1]); replace x[j+1] with a fresh token s'; a true
    inductor's argmax at i FOLLOWS to s'. All rows' swapped sequences are batched into ONE forward."""
    model.eval()
    x = x.to(device)
    B, T = x.shape
    g = torch.Generator().manual_seed(seed + 4242)
    xs = x.clone()
    rows, qpos, sps = [], [], []
    for b in range(B):
        qs = [i for i in range(T - 1) if int(t[b, i]) != IGNORE]
        if not qs:
            continue
        i = qs[-1]
        c = int(x[b, i])
        js = [j for j in range(i) if int(x[b, j]) == c]
        if not js or js[-1] + 1 >= T:
            continue
        j = js[-1]
        orig = int(x[b, j + 1])
        sp = int(torch.randint(0, cfg.K, (1,), generator=g))
        if sp == orig:
            sp = (sp + 1) % cfg.K
        xs[b, j + 1] = sp
        rows.append(b); qpos.append(i); sps.append(sp)
    if not rows:
        return 0.0
    with torch.no_grad():
        logits, _ = model(xs[:, :-1])
    pred = logits[rows, qpos].argmax(-1).tolist()
    return sum(int(p == sp) for p, sp in zip(pred, sps)) / len(rows)


def _induction_scores(cfg: InductionConfig, model: MiniGPT, x: torch.Tensor, t: torch.Tensor,
                      device) -> dict:
    """Mechanistic readout. Per layer: mass an inductable query i places on the MOST-RECENT
    successor position (j+1, the position that defines the target), summed over heads, minus the
    uniform baseline 1/(i+1). Plus a layer-0 prev-token score (mass i -> i-1)."""
    model.eval()
    x = x.to(device)
    B, T = x.shape
    model.set_attention_capture(True)
    with torch.no_grad():
        model(x[:, :-1])
    maps = model.attention_maps()
    model.set_attention_capture(False)
    succ_by_layer = []
    for att in maps:
        H = att.shape[1]
        ssum = scnt = 0.0
        for b in range(B):
            last = {}
            for i in range(T - 1):
                c = int(x[b, i])
                if int(t[b, i]) != IGNORE and c in last:
                    src = last[c] + 1
                    if src <= i:
                        ssum += sum(att[b, h, i, src].item() for h in range(H)) - 1.0 / (i + 1)
                        scnt += 1
                last[c] = i
        succ_by_layer.append(ssum / max(scnt, 1))
    prev_tok = 0.0
    if maps:
        att0 = maps[0]; H = att0.shape[1]
        ps = pc = 0.0
        for b in range(B):
            for i in range(1, T - 1):
                ps += sum(att0[b, h, i, i - 1].item() for h in range(H)); pc += 1
        prev_tok = ps / max(pc, 1)
    return {"succ_mass_by_layer": [round(v, 5) for v in succ_by_layer],
            "best_layer_succ_mass": round(max(succ_by_layer), 5) if succ_by_layer else 0.0,
            "layer0_prev_token": round(prev_tok, 5)}


def train_arm(cfg: InductionConfig, depth: int, width: int, attn_only: bool, mode: str,
              eval_x, eval_t, seed: int, device, mech_x=None, mech_t=None) -> dict:
    """Train one arm with FRESH per-step data (no finite-data pool -> no large-model overfitting);
    log the inductable-acc trajectory on ``eval_x/eval_t`` and (when mech sets are given) the causal
    + mechanistic readouts."""
    model = make_model(cfg, depth, width, attn_only, seed).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, betas=(cfg.beta1, cfg.beta2),
                            weight_decay=cfg.weight_decay)
    gen = torch.Generator(device=device).manual_seed(seed + 11)
    traj = []
    for step in range(cfg.steps + 1):
        if step % cfg.eval_every == 0:
            traj.append(round(_inductable_acc(model, eval_x, eval_t, device), 5))
        if step == cfg.steps:
            break
        x, tg = make_batch(cfg, cfg.batch, gen, device, mode=mode)
        model.train(); opt.zero_grad(set_to_none=True)
        _, loss = model(x[:, :-1], tg)
        loss.backward(); opt.step()
    out = {"acc": _inductable_acc(model, eval_x, eval_t, device), "traj": traj}
    if mech_x is not None:
        out["swap_follow"] = _swap_follow(cfg, model, mech_x, mech_t, device, seed)
        out.update(_induction_scores(cfg, model, mech_x, mech_t, device))
    else:
        out.update({"swap_follow": float("nan"), "best_layer_succ_mass": float("nan"),
                    "succ_mass_by_layer": [], "layer0_prev_token": float("nan")})
    return out


def run_phase_a(cfg: InductionConfig, device) -> dict:
    """Single training pass -> cache. FRESH per-step data; shared eval/mech sets; analytic unigram
    baseline + random-init gate once. Arms: clean depth x width; 1-layer fixed-offset shortcut
    control (capability); attention-only (MLP zeroed) depth x width."""
    ge = torch.Generator(device=device).manual_seed(20240)
    eval_x, eval_t = [], []
    for _ in range(cfg.eval_n_batches):
        x, tg = make_batch(cfg, cfg.eval_batch, ge, device, mode="clean")
        eval_x.append(x.cpu()); eval_t.append(tg.cpu())
    gef = torch.Generator(device=device).manual_seed(20241)
    fx_eval_x, fx_eval_t = [], []
    for _ in range(cfg.eval_n_batches):
        x, tg = make_batch(cfg, cfg.eval_batch, gef, device, mode="fixed_offset")
        fx_eval_x.append(x.cpu()); fx_eval_t.append(tg.cpu())
    gm = torch.Generator(device=device).manual_seed(20242)
    mx, mt = make_batch(cfg, cfg.mech_batch, gm, device, mode="clean")
    mech_x, mech_t = mx.cpu(), mt.cpu()

    uni_acc, max_marg = unigram_acc(cfg, eval_x[0], eval_t[0])
    rand_model = make_model(cfg, depth=2, width=cfg.widths[-1], attn_only=False, seed=999).to(device)
    random_init_acc = _inductable_acc(rand_model, eval_x, eval_t, device)

    clean: dict = {}
    for depth in cfg.depths:
        for width in cfg.widths:
            for seed in cfg.seeds:
                clean.setdefault((depth, width), {})[seed] = train_arm(
                    cfg, depth, width, False, "clean", eval_x, eval_t, seed,
                    device, mech_x=mech_x, mech_t=mech_t)

    shortcut: dict = {}   # 1-layer trained AND evaluated on the positional task (capability control)
    for width in cfg.shortcut_widths:
        for seed in cfg.seeds:
            shortcut.setdefault(width, {})[seed] = train_arm(
                cfg, 1, width, False, "fixed_offset", fx_eval_x, fx_eval_t, seed, device)

    attn_only: dict = {}
    for depth in cfg.depths:
        for width in cfg.attn_only_widths:
            for seed in cfg.seeds:
                attn_only.setdefault((depth, width), {})[seed] = train_arm(
                    cfg, depth, width, True, "clean", eval_x, eval_t, seed, device)

    return {
        "config": {"K": cfg.K, "T": cfg.T, "widths": list(cfg.widths), "depths": list(cfg.depths),
                   "shortcut_widths": list(cfg.shortcut_widths), "attn_only_widths": list(cfg.attn_only_widths),
                   "steps": cfg.steps, "seeds": list(cfg.seeds), "n_head": cfg.n_head},
        "chance": cfg.chance, "ceiling": cfg.ceiling, "S": cfg.S,
        "unigram_acc": uni_acc, "max_marginal": max_marg, "random_init_acc": random_init_acc,
        "clean": {f"d{d}w{w}": clean[(d, w)] for (d, w) in clean},
        "shortcut": {f"w{w}": shortcut[w] for w in shortcut},
        "attn_only": {f"d{d}w{w}": attn_only[(d, w)] for (d, w) in attn_only},
    }


# ------------------------------------------------------------------------------- analysis
def _wstar(widths: list[int], acc_by_width: list[float], S: float) -> float:
    for i, (w, v) in enumerate(zip(widths, acc_by_width)):
        if v >= S:
            if i == 0:
                return float(w)
            w0, v0 = widths[i - 1], acc_by_width[i - 1]
            if v == v0:
                return float(w)
            return float(w0 + (S - v0) / (v - v0) * (w - w0))
    return float("inf")


def summarize(cache: dict, cfg: InductionConfig | None = None) -> dict:
    cfg = cfg or InductionConfig()
    seeds = cache["config"]["seeds"]
    widths = cache["config"]["widths"]
    depths = cache["config"]["depths"]
    S = cache["S"]

    def carm(d, w):
        return cache["clean"][f"d{d}w{w}"]

    cells = {}
    for d in depths:
        for w in widths:
            recs = carm(d, w)
            cells[(d, w)] = {
                "acc": mean_std([recs[s]["acc"] for s in seeds]),
                "swap_follow": mean_std([recs[s]["swap_follow"] for s in seeds]),
                "best_layer_succ_mass": mean_std([recs[s]["best_layer_succ_mass"] for s in seeds]),
                "layer0_prev_token": mean_std([recs[s]["layer0_prev_token"] for s in seeds]),
            }
    wstar = {d: {s: _wstar(widths, [carm(d, w)[s]["acc"] for w in widths], S) for s in seeds} for d in depths}
    wstar_ms = {d: mean_std([wstar[d][s] for s in seeds if math.isfinite(wstar[d][s])]) for d in depths}
    wstar_finite_frac = {d: sum(math.isfinite(wstar[d][s]) for s in seeds) / len(seeds) for d in depths}

    shortcut = {w: mean_std([cache["shortcut"][f"w{w}"][s]["acc"] for s in seeds])
                for w in cache["config"]["shortcut_widths"]}
    attn_only = {}
    for d in depths:
        for w in cache["config"]["attn_only_widths"]:
            key = f"d{d}w{w}"
            if key in cache["attn_only"]:
                attn_only[(d, w)] = mean_std([cache["attn_only"][key][s]["acc"] for s in seeds])

    return {
        "config": cache["config"], "chance": cache["chance"], "ceiling": cache["ceiling"], "S": S,
        "unigram_acc": cache["unigram_acc"], "max_marginal": cache["max_marginal"],
        "random_init_acc": cache["random_init_acc"],
        "seeds": seeds, "widths": widths, "depths": depths,
        "cells": cells, "wstar": wstar, "wstar_ms": wstar_ms, "wstar_finite_frac": wstar_finite_frac,
        "shortcut": shortcut, "attn_only": attn_only,
    }


# Verdict vocabulary and gate logic live in a focused pure module.
def decide(result: dict, cfg: InductionConfig | None = None) -> dict:
    """Apply the pre-registered induction verdict ladder."""
    return decide_induction(result, cfg or InductionConfig())


# ------------------------------------------------------------------------------- report
def build_report(result: dict, info: dict, source: str, *, generated_at: str | None = None) -> dict:
    """Assemble the stable v1196 report contract."""
    return build_induction_report(
        result,
        info,
        source,
        generated_at=generated_at,
        unigram_margin=InductionConfig().unigram_margin,
    )


__all__ = [
    "InductionConfig", "make_batch", "unigram_acc", "make_model", "train_arm", "run_phase_a",
    "summarize", "decide", "build_report", "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
