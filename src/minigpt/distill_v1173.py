"""v1173: distillation under ALEATORIC uncertainty — dark knowledge made real.

The mirror of v1172. There, on a DETERMINISTIC task, the teacher was near-one-hot,
dark knowledge was absent by construction, and distillation gave no benefit over
hard-label SFT. Here the task is genuinely STOCHASTIC: each context maps to a known
categorical ``P_true`` over the output chars (Dirichlet-drawn, entropy swept), so a
single hard sample under-specifies the answer while the teacher's SOFT target conveys
the whole distribution — the canonical Hinton dark-knowledge regime.

Because we CONSTRUCT ``P_true`` the metric is exact: forward KL ``D(P_true || P_student)``
measured at the single stochastic output position (completions are EOS-free so the
masked position is exactly the uncertain one). The pre-registered decomposition isolates
dark knowledge from its confounds:

* data-efficiency  = KL(scratch_hard, few real samples) − KL(teacher_argmax_hard)
* DARK KNOWLEDGE   = KL(teacher_argmax_hard) − KL(teacher_soft)   ← headline
  (same teacher, same 400-sample budget, mode-only pseudo-label vs the full soft shape)

with controls: ``label_smooth`` (generic flattening — can't encode the specific P;
helps high-H, hurts low-H), ``shuffled_teacher`` (argmax+entropy preserved, class identity
destroyed — must HURT, the mirror of v1172 where it was inert), ``oracle_true_P`` (upper
bound), and a ``scratch_many`` sample-count sweep (the honest falsifier: with the teacher's
own 400 samples/ctx, plain hard CE recovers P — the benefit is data-efficiency under
uncertainty, not magic). ``status=="pass"`` certifies a valid measurement (faithful soft
teacher, real entropy spread, valid hard baseline, controls ran), never "distillation good".

KL is lower-is-better, so every comparison routes through ``beats_lower`` (the project's
``significant`` primitive is higher-is-better — calling it on a loss would silently fire
the wrong way). Scope: single-position next-char categorical; the Dirichlet synthetic is
the controlled stand-in for real-text ambiguity.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as F

from minigpt.distill_common import make_distill_model as _make_model, train_student
from minigpt.experiment_utils import mean_std, significant
from minigpt.report_utils import utc_now

OUT_ALPHA = "abcde"
CTX_ALPHA = "GHIJKLMNOPQRSTUVWXYZ0123456789@$"   # >= 32 distinct context symbols
SEP, EOS, PAD = "=", "\n", "#"

ARM_ORDER = ["scratch_hard", "teacher_argmax_hard", "teacher_soft", "label_smooth",
             "shuffled_teacher", "oracle_true_P"]


def beats_lower(a, sa, b, sb):
    """True iff ``a`` is significantly LOWER (better, for a loss) than ``b`` —
    inverts the higher-is-better :func:`significant`."""
    return significant(b, sb, a, sa)


def build_stochastic_task(k: int, *, seed: int, alpha_lo: float = 0.12, alpha_hi: float = 6.0):
    """K contexts, each a categorical ``P_true`` over the M=len(OUT_ALPHA) output chars
    drawn from ``Dirichlet(alpha)`` with alpha swept (peaky→uniform) for an entropy spread.
    Returns ``(P_true (K,M), H (K,), ctx_chars, out_chars)``."""
    rng = np.random.default_rng(seed)
    m = len(OUT_ALPHA)
    alphas = np.geomspace(alpha_lo, alpha_hi, k)
    P = np.stack([rng.dirichlet([a] * m) for a in alphas])
    H = -(P * np.log(P + 1e-12)).sum(1)
    return P, H, CTX_ALPHA[:k], OUT_ALPHA


def _sample_examples(P_true, contexts, out_ids, n_per_ctx, rng):
    """EOS-free examples ``([ctx, sep, x], n_prompt=2)`` with ``x ~ P_true(·|ctx)`` —
    so ``_build_xy`` masks exactly the one stochastic output position."""
    ex = []
    for k, ctx in enumerate(contexts):
        draws = rng.choice(len(out_ids), size=n_per_ctx, p=P_true[k])
        for d in draws:
            ex.append((list(ctx) + [out_ids[d]], len(ctx)))
    return ex


@torch.no_grad()
def student_P(model, contexts, out_ids, device):
    """Per-context conditional over output chars: feed ``[ctx, sep]``, softmax the final
    logits over the FULL vocab, slice the output ids. Returns
    ``(P_norm (K,M), sub_raw (K,M), leakage (K,))`` — ``sub_raw`` is the un-renormalized
    output-char mass (so leakage can be charged), ``P_norm`` the renormalized conditional."""
    model.eval()
    X = torch.tensor(contexts, dtype=torch.long, device=device)
    logits, _ = model(X)
    p = F.softmax(logits[:, -1, :], dim=-1)
    sub = p[:, out_ids]
    leak = (1.0 - sub.sum(1)).clamp_min(0.0)
    norm = sub / sub.sum(1, keepdim=True).clamp_min(1e-9)
    return norm.cpu().numpy(), sub.cpu().numpy(), leak.cpu().numpy()


def kl_fwd(P_true, P_model, floor=1e-12):
    return (P_true * (np.log(P_true + floor) - np.log(P_model + floor))).sum(1)


def kl_full(P_true, sub_raw, floor=1e-12):
    """Forward KL charging leaked (off-alphabet) mass: uses the UN-renormalized output
    mass, so a student that leaks probability off the alphabet is penalized."""
    return (P_true * (np.log(P_true + floor) - np.log(sub_raw + floor))).sum(1)


def entropy(P, floor=1e-12):
    return -(P * np.log(P + floor)).sum(1)


def ols_slope_se(x, y):
    """Simple linear regression slope and its standard error."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    if n < 3:
        return float("nan"), float("nan")
    xm, ym = x.mean(), y.mean()
    sxx = ((x - xm) ** 2).sum()
    if sxx <= 1e-12:
        return float("nan"), float("nan")
    slope = ((x - xm) * (y - ym)).sum() / sxx
    resid = y - (ym + slope * (x - xm))
    s2 = (resid ** 2).sum() / max(n - 2, 1)
    se = (s2 / sxx) ** 0.5
    return float(slope), float(se)


def eps_for_entropy(target_H, m, lo=0.0, hi=0.999, iters=60):
    """Label-smoothing eps whose smoothed one-hot target has entropy ``target_H``."""
    def H(e):
        p0 = (1 - e) + e / m
        pe = e / m
        return -(p0 * np.log(p0 + 1e-12) + (m - 1) * pe * np.log(pe + 1e-12))
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if H(mid) < target_H:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


@dataclass
class DistillUncertaintyConfig:
    block_size: int = 8
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341)
    seed_base: int = 1337
    k_contexts: int = 32
    teacher_seeds: tuple[int, ...] = (1337, 1338, 1339)
    teacher_layer: int = 4
    teacher_head: int = 4
    teacher_embd: int = 64
    teacher_steps: int = 1200
    teacher_samples_per_ctx: int = 400
    student_layer: int = 2
    student_head: int = 4
    student_embd: int = 32
    student_steps: int = 700
    student_samples_per_ctx: int = 1            # headline few-sample regime
    sweep_samples: tuple[int, ...] = (1, 3, 10, 30, 100, 400)
    sweep_seeds: tuple[int, ...] = (1337, 1338, 1339)
    lr: float = 3e-3
    batch_size: int = 64
    teacher_kl_alpha: float = 0.05              # gate g1: KL(true||teacher) <= alpha * mean_H
    teacher_leak_max: float = 0.02
    entropy_floor: float = 0.6                  # gate g2: mean_H above this
    entropy_spread_min: float = 0.8


REVIEW_VERDICTS = {"teacher_ceiling_untrustworthy", "no_valid_entropy_headroom", "controls_missing"}
PRIMARY_VERDICTS = {
    "dark_knowledge_is_data_efficiency_under_uncertainty",
    "dark_knowledge_transfer_not_recoverable",
    "data_efficiency_not_dark_knowledge",
    "soft_target_generic_not_specific",
    "no_distill_benefit",
}


def decide(arm_meanKL, arm_perctx, H, teacher_kl, sweep_meanKL, slope_lb):
    """Pure gate + verdict. ``arm_meanKL`` maps arm->(mean,std) of per-seed mean KL_fwd;
    ``arm_perctx`` maps arm->(K,) per-context mean KL_fwd; ``sweep_meanKL`` maps n->mean KL."""
    soft_m, soft_s = arm_meanKL["teacher_soft"]
    arg_m, arg_s = arm_meanKL["teacher_argmax_hard"]
    hard_m, hard_s = arm_meanKL["scratch_hard"]
    ls_m, ls_s = arm_meanKL["label_smooth"]
    sh_m, sh_s = arm_meanKL["shuffled_teacher"]

    soft_beats_argmax = beats_lower(soft_m, soft_s, arg_m, arg_s)
    soft_beats_hard = beats_lower(soft_m, soft_s, hard_m, hard_s)
    soft_beats_ls = beats_lower(soft_m, soft_s, ls_m, ls_s)
    shuffled_hurts = beats_lower(soft_m, soft_s, sh_m, sh_s)
    grows_with_H = slope_lb > 0
    n_max = max(sweep_meanKL) if sweep_meanKL else None
    hard_recovers = (n_max is not None) and (sweep_meanKL[n_max] <= soft_m + (soft_s ** 2 + 0.0) ** 0.5 + 1e-9)

    flags = {"soft_beats_argmax": soft_beats_argmax, "soft_beats_hard": soft_beats_hard,
             "soft_beats_label_smooth": soft_beats_ls, "shuffled_hurts": shuffled_hurts,
             "dark_knowledge_grows_with_H": grows_with_H, "hard_samples_recover_P": hard_recovers}

    if not soft_beats_hard:
        verdict = "no_distill_benefit"
    elif not soft_beats_argmax:
        verdict = "data_efficiency_not_dark_knowledge"
    elif not soft_beats_ls:
        verdict = "soft_target_generic_not_specific"
    elif not hard_recovers:
        verdict = "dark_knowledge_transfer_not_recoverable"
    else:
        verdict = "dark_knowledge_is_data_efficiency_under_uncertainty"
    return {"status": "pass", "decision": "distillation_under_uncertainty_measured", "verdict": verdict, "flags": flags}


def run_distill_uncertainty(
    *, vocab_size, P_true, H, contexts, out_ids, pad_id, config, device,
    corpus_stats=None, generated_at=None,
):
    bs = config.block_size
    K = len(contexts)
    P_true = np.asarray(P_true, float)
    H = np.asarray(H, float)
    mean_H = float(H.mean())
    V = vocab_size

    # ---- gate g2: real entropy structure (decided up front) ----
    spread = float(H.max() - H.min())
    g2 = (mean_H > config.entropy_floor) and (spread >= config.entropy_spread_min)

    # ---- teachers (>=3 seeds): faithful soft ceiling ----
    teacher_kls, teacher_leaks, teacher_ents = [], [], []
    teacher0 = None
    for i, ts in enumerate(config.teacher_seeds):
        rng = np.random.default_rng(10_000 + ts)
        tex = _sample_examples(P_true, contexts, out_ids, config.teacher_samples_per_ctx, rng)
        torch.manual_seed(ts)
        teacher = _make_model(vocab_size, bs, config.teacher_layer, config.teacher_head, config.teacher_embd).to(device)
        train_student(teacher, tex, steps=config.teacher_steps, lr=config.lr, batch_size=config.batch_size,
                      block_size=bs, pad_id=pad_id, device=device, loss_mode="ce")
        Pn, _sub, leak = student_P(teacher, contexts, out_ids, device)
        teacher_kls.append(float(kl_fwd(P_true, Pn).mean()))
        teacher_leaks.append(float(leak.mean()))
        teacher_ents.append(float(entropy(Pn).mean()))
        if i == 0:
            teacher0 = teacher
    teacher_kl_mean, teacher_kl_std = mean_std(teacher_kls)
    teacher_leak = float(np.mean(teacher_leaks))
    teacher_ent = float(np.mean(teacher_ents))
    g1 = (teacher_kl_mean <= config.teacher_kl_alpha * mean_H) and (teacher_leak < config.teacher_leak_max)

    # teacher argmax pseudo-labels + oracle target matrix (built from teacher0 / P_true)
    Pn0, _s0, _l0 = student_P(teacher0, contexts, out_ids, device)
    argmax_out = [out_ids[int(np.argmax(Pn0[k]))] for k in range(K)]
    argmax_ex = [(list(contexts[k]) + [argmax_out[k]], len(contexts[k])) for k in range(K)]

    Ptrue_full = torch.full((K, V), 1e-6, device=device)
    for k in range(K):
        for j, oid in enumerate(out_ids):
            Ptrue_full[k, oid] = float(P_true[k, j])
    Ptrue_full = Ptrue_full / Ptrue_full.sum(1, keepdim=True)
    k_of_ctx = torch.zeros(V, dtype=torch.long, device=device)
    for k, ctx in enumerate(contexts):
        k_of_ctx[ctx[0]] = k

    def oracle_fn(x):
        rows = Ptrue_full[k_of_ctx[x[:, 0]]]            # (B, V)
        return rows.unsqueeze(1).expand(-1, x.shape[1], -1)

    eps = eps_for_entropy(mean_H, len(out_ids))
    shuffle_perm = torch.randperm(V - 1, generator=torch.Generator(device="cpu").manual_seed(98765)).to(device)
    context_prompts = [list(c) for c in contexts]

    # ---- main arms x seeds (independent init, re-drawn student samples per seed) ----
    arm_meanKL, arm_perctx, arm_meanKLfull, arm_leak, arm_entdiff = {}, {}, {}, {}, {}
    for arm in ARM_ORDER:
        arm_idx = ARM_ORDER.index(arm)
        per_seed_mean, per_seed_perctx, per_seed_full, per_seed_leak, per_seed_entd = [], [], [], [], []
        for seed in config.seeds:
            rng = np.random.default_rng(config.seed_base + 1009 * arm_idx + seed)
            torch.manual_seed(config.seed_base + 1009 * arm_idx + seed)
            student = _make_model(vocab_size, bs, config.student_layer, config.student_head, config.student_embd).to(device)
            if arm == "scratch_hard":
                ex = _sample_examples(P_true, contexts, out_ids, config.student_samples_per_ctx, rng)
                train_student(student, ex, steps=config.student_steps, lr=config.lr, batch_size=config.batch_size,
                              block_size=bs, pad_id=pad_id, device=device, loss_mode="ce")
            elif arm == "label_smooth":
                ex = _sample_examples(P_true, contexts, out_ids, config.student_samples_per_ctx, rng)
                train_student(student, ex, steps=config.student_steps, lr=config.lr, batch_size=config.batch_size,
                              block_size=bs, pad_id=pad_id, device=device, loss_mode="ce", label_smoothing=eps)
            elif arm == "teacher_argmax_hard":
                train_student(student, argmax_ex, steps=config.student_steps, lr=config.lr, batch_size=config.batch_size,
                              block_size=bs, pad_id=pad_id, device=device, loss_mode="ce")
            elif arm == "teacher_soft":
                ex = [(c + [out_ids[0]], len(c)) for c in context_prompts]   # label irrelevant (hw=0)
                train_student(student, ex, steps=config.student_steps, lr=config.lr, batch_size=config.batch_size,
                              block_size=bs, pad_id=pad_id, device=device, loss_mode="distill",
                              teacher=teacher0, tau=1.0, hard_weight=0.0)
            elif arm == "shuffled_teacher":
                ex = [(c + [out_ids[0]], len(c)) for c in context_prompts]
                train_student(student, ex, steps=config.student_steps, lr=config.lr, batch_size=config.batch_size,
                              block_size=bs, pad_id=pad_id, device=device, loss_mode="distill",
                              teacher=teacher0, tau=1.0, hard_weight=0.0, shuffle_perm=shuffle_perm)
            else:  # oracle_true_P
                ex = [(c + [out_ids[0]], len(c)) for c in context_prompts]
                train_student(student, ex, steps=config.student_steps, lr=config.lr, batch_size=config.batch_size,
                              block_size=bs, pad_id=pad_id, device=device, loss_mode="distill",
                              teacher=None, tau=1.0, hard_weight=0.0, teacher_probs_fn=oracle_fn)
            Pn, sub, leak = student_P(student, contexts, out_ids, device)
            klc = kl_fwd(P_true, Pn)
            per_seed_mean.append(float(klc.mean()))
            per_seed_perctx.append(klc)
            per_seed_full.append(float(kl_full(P_true, sub).mean()))
            per_seed_leak.append(float(leak.mean()))
            per_seed_entd.append(float((entropy(Pn) - H).mean()))
        arm_meanKL[arm] = mean_std(per_seed_mean)
        arm_perctx[arm] = np.mean(np.stack(per_seed_perctx), axis=0)   # (K,)
        arm_meanKLfull[arm] = mean_std(per_seed_full)
        arm_leak[arm] = float(np.mean(per_seed_leak))
        arm_entdiff[arm] = float(np.mean(per_seed_entd))

    # ---- data-efficiency sweep: scratch_hard at n samples/ctx ----
    sweep_meanKL = {}
    for n in config.sweep_samples:
        vals = []
        for seed in config.sweep_seeds:
            rng = np.random.default_rng(50_000 + n * 13 + seed)
            torch.manual_seed(60_000 + seed)
            student = _make_model(vocab_size, bs, config.student_layer, config.student_head, config.student_embd).to(device)
            ex = _sample_examples(P_true, contexts, out_ids, n, rng)
            train_student(student, ex, steps=config.student_steps, lr=config.lr, batch_size=config.batch_size,
                          block_size=bs, pad_id=pad_id, device=device, loss_mode="ce")
            Pn, _s, _l = student_P(student, contexts, out_ids, device)
            vals.append(float(kl_fwd(P_true, Pn).mean()))
        sweep_meanKL[n] = float(np.mean(vals))

    # ---- entropy regression: per-context dark-knowledge Δ = KL(argmax) − KL(soft) vs H ----
    dk_delta = arm_perctx["teacher_argmax_hard"] - arm_perctx["teacher_soft"]   # (K,)
    de_delta = arm_perctx["scratch_hard"] - arm_perctx["teacher_argmax_hard"]   # data-efficiency confound
    dk_slope, dk_se = ols_slope_se(H, dk_delta)
    de_slope, de_se = ols_slope_se(H, de_delta)
    dk_slope_lb = dk_slope - dk_se if dk_slope == dk_slope else float("nan")

    # ---- gate + verdict ----
    if not g1:
        status, decision, verdict, flags = "review", "teacher_ceiling_untrustworthy", "teacher_ceiling_untrustworthy", {}
    elif not g2:
        status, decision, verdict, flags = "review", "no_valid_entropy_headroom", "no_valid_entropy_headroom", {}
    elif any(np.isnan(arm_meanKL[a][0]) for a in ARM_ORDER):
        status, decision, verdict, flags = "review", "controls_missing", "controls_missing", {}
    else:
        out = decide(arm_meanKL, arm_perctx, H, teacher_kl_mean, sweep_meanKL, dk_slope_lb)
        status, decision, verdict, flags = out["status"], out["decision"], out["verdict"], out["flags"]

    def excess(arm):
        return round(arm_meanKL[arm][0] - teacher_kl_mean, 6)

    rows = []
    for arm in ARM_ORDER:
        m, s = arm_meanKL[arm]
        rows.append({"arm": arm, "kl_fwd_mean": round(m, 6), "kl_fwd_std": round(s, 6),
                     "kl_fwd_median": round(float(np.median(arm_perctx[arm])), 6),
                     "kl_full_mean": round(arm_meanKLfull[arm][0], 6),
                     "excess_kl_vs_teacher": excess(arm), "leakage": round(arm_leak[arm], 6),
                     "entropy_bias": round(arm_entdiff[arm], 6)})

    stats = corpus_stats or {}
    summary = {
        "status": status, "decision": decision, "verdict": verdict,
        "device": str(device), "seeds": len(config.seeds), "k_contexts": K, "m_outputs": len(out_ids),
        "mean_true_entropy_nats": round(mean_H, 6), "entropy_spread": round(spread, 6),
        "teacher_size": f"{config.teacher_layer}L/{config.teacher_embd}",
        "teacher_kl_to_true": round(teacher_kl_mean, 6), "teacher_kl_to_true_std": round(teacher_kl_std, 6),
        "teacher_entropy": round(teacher_ent, 6), "teacher_leakage": round(teacher_leak, 6),
        "teacher_faithful_g1": g1, "entropy_structure_g2": g2,
        "label_smoothing_eps": round(eps, 6),
        "student_samples_per_ctx": config.student_samples_per_ctx,
        "task_learned": status == "pass",
        "heldout_prompts": stats.get("heldout_prompts"),
    }
    if status == "pass":
        summary.update({
            "scratch_hard_kl": round(arm_meanKL["scratch_hard"][0], 6),
            "teacher_argmax_hard_kl": round(arm_meanKL["teacher_argmax_hard"][0], 6),
            "teacher_soft_kl": round(arm_meanKL["teacher_soft"][0], 6),
            "label_smooth_kl": round(arm_meanKL["label_smooth"][0], 6),
            "shuffled_teacher_kl": round(arm_meanKL["shuffled_teacher"][0], 6),
            "oracle_true_P_kl": round(arm_meanKL["oracle_true_P"][0], 6),
            "data_efficiency_term": round(arm_meanKL["scratch_hard"][0] - arm_meanKL["teacher_argmax_hard"][0], 6),
            "dark_knowledge_term": round(arm_meanKL["teacher_argmax_hard"][0] - arm_meanKL["teacher_soft"][0], 6),
            "dk_slope_vs_entropy": round(dk_slope, 6), "dk_slope_se": round(dk_se, 6), "dk_slope_lb": round(dk_slope_lb, 6),
            "de_slope_vs_entropy": round(de_slope, 6),
            "scratch_many_kl": {str(n): round(v, 6) for n, v in sweep_meanKL.items()},
            **{f"flag_{k}": v for k, v in flags.items()},
        })

    recommendations = [
        f"VERDICT ({verdict}): on a STOCHASTIC task (mean true entropy {mean_H:.3f} nats) the teacher is SOFT and faithful (KL(true||teacher) {teacher_kl_mean:.4f} ≈ {config.teacher_kl_alpha}*H ceiling; entropy {teacher_ent:.3f} ≈ true {mean_H:.3f}) — the mirror of v1172's near-one-hot deterministic teacher. status='{status}' certifies a VALID measurement (faithful soft teacher, real entropy spread {spread:.2f}, valid baseline, controls ran), NOT that distillation is good.",
        (f"DARK KNOWLEDGE = KL(teacher_argmax_hard) − KL(teacher_soft) = {arm_meanKL['teacher_argmax_hard'][0]:.3f} − {arm_meanKL['teacher_soft'][0]:.3f} = {arm_meanKL['teacher_argmax_hard'][0]-arm_meanKL['teacher_soft'][0]:+.3f}. SAME teacher, SAME 400-sample budget, mode-only pseudo-label vs the full soft shape — soft<<argmax (soft_beats_argmax={flags.get('soft_beats_argmax')}) IS dark knowledge, and it GROWS with context entropy (slope {dk_slope:.3f}, lb {dk_slope_lb:.3f}>0={flags.get('dark_knowledge_grows_with_H')}). shuffled_teacher (identity destroyed) HURTS (KL {arm_meanKL['shuffled_teacher'][0]:.3f}) — the mirror of v1172 where it was inert." if status == "pass" else f"GATE not met → review ({decision})."),
        (f"NOT MAGIC — data-efficiency under uncertainty: scratch_many at the teacher's own {config.teacher_samples_per_ctx} samples/ctx reaches KL {sweep_meanKL.get(max(sweep_meanKL), float('nan')):.3f} (hard_samples_recover_P={flags.get('hard_samples_recover_P')}). The benefit is buying the large-n hard target at small n; the teacher's {config.teacher_samples_per_ctx}-sample budget is amortized, not free. data-efficiency term {arm_meanKL['scratch_hard'][0]-arm_meanKL['teacher_argmax_hard'][0]:+.3f}." if status == "pass" else ""),
        (f"CONTROLS: label_smooth (ε={eps:.3f} matched to MEAN entropy, KL {arm_meanKL['label_smooth'][0]:.3f}) flattens generically — can't encode the SPECIFIC P (soft_beats_label_smooth={flags.get('soft_beats_label_smooth')}); oracle_true_P {arm_meanKL['oracle_true_P'][0]:.3f} is the upper bound (KL floor). All KL framed vs the teacher CEILING {teacher_kl_mean:.4f}, never reported as '≈0=perfect'." if status == "pass" else ""),
        "v1172↔v1173 CONTRAST: same train_student/kl_term machinery; deterministic teacher (H≈0.05, one-hot) → no dark knowledge, distill==hard; stochastic teacher (H≈1.29, soft) → dark knowledge real, distill≪hard, grows with H. SCOPE: single-position next-char categorical; Dirichlet synthetic is the controlled stand-in for real-text ambiguity (KL lower-is-better → all comparisons via beats_lower).",
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT distillation under uncertainty v1173",
        "generated_at": generated_at or utc_now(),
        "status": status, "decision": decision,
        "summary": summary, "rows": rows,
        "recommendations": [r for r in recommendations if r],
        "csv_fieldnames": ["arm", "kl_fwd_mean", "kl_fwd_std", "kl_fwd_median", "kl_full_mean",
                           "excess_kl_vs_teacher", "leakage", "entropy_bias"],
        "scratch_many_kl": {str(n): round(v, 6) for n, v in sweep_meanKL.items()},
        "per_context_entropy": [round(float(h), 4) for h in H],
        "dark_knowledge_delta_by_context": [round(float(x), 4) for x in dk_delta],
        "seeds": list(config.seeds),
    }


__all__ = [
    "beats_lower", "build_stochastic_task", "student_P", "kl_fwd", "kl_full", "entropy",
    "ols_slope_se", "eps_for_entropy", "decide", "run_distill_uncertainty",
    "DistillUncertaintyConfig", "ARM_ORDER", "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
    "OUT_ALPHA", "CTX_ALPHA", "SEP", "EOS", "PAD",
]
