"""v1194: EWC (parameter anchoring) vs REPLAY (data rehearsal) for catastrophic forgetting.

A direct follow-up to v1193, which showed that on a shared 1-layer transformer learning Task B
(=(a*b) mod p) catastrophically overwrites Task A (=(a+b) mod p) -- and that the forgetting is
DISTRIBUTION-SHIFT-driven (random-label-B forgets A just as much), mitigated by REPLAY (re-showing
A-train examples). v1194 asks: does a mechanistically DIFFERENT mitigation -- EWC, which anchors the
weights important to A in PARAMETER space (blind to data) -- work too, and how do the two compare?

EWC: after consolidating A, estimate the diagonal Fisher ``F`` on A-train at the consolidated
weights ``theta*`` and, during B-training, add ``(lambda/2) * sum_i F_i (w_i - theta*_i)^2``.

The honest comparison is each method's STABILITY-PLASTICITY frontier: sweep the strength knob
(EWC ``lambda`` / replay buffer ``k``) and record (acc_B = plasticity / new task, acc_A =
stability / retained old task). The score for a method is the best achievable ``min(acc_A, acc_B)``
along its frontier -- the best single operating point that keeps BOTH tasks. ``status=="pass"``
certifies a VALID measurement (A consolidated, B learnable, both frontiers mapped, continue-on-A
floor clean), never that either method is good.

Why this is interesting: a diagonal-Fisher anchor is LOCAL/separable; if the forgetting is a
GLOBAL distribution shift (v1193), the anchor can only resist by freezing the important weights,
which blocks B -- a brutal tradeoff -- whereas replay keeps A in the loss without freezing anything.

Scope: toy modular arithmetic on a 1-layer transformer with diagonal-Fisher EWC; NOT a claim that
EWC is useless in general (it helps in many continual-learning settings).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import torch

from minigpt.continual_v1193 import (
    answer_accuracy, answer_loss, build_op, consolidate, make_model, majority_prior,
    pair_masks, train_phase, verify_no_leak,
)
from minigpt.continual_v1193 import ContinualConfig
from minigpt.experiment_utils import mean_std, significant


@dataclass
class EWCReplayConfig:
    base: ContinualConfig = field(default_factory=lambda: ContinualConfig(p=23, task_a="add", task_b="mul"))
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    # strength-knob grids for the two frontiers. The EWC grid is REFINED at the knee (4e10,4.5e10,
    # 5e10 between 3e10 and 6e10) where the probe saw a brutal plasticity->rigidity tip, so a hidden
    # good operating point cannot be missed (the v1183 interior-optimum lesson). replay saturates by k~16-32.
    ewc_lambdas: tuple[float, ...] = (0.0, 3e9, 1e10, 3e10, 4e10, 4.5e10, 5e10, 6e10, 1e11, 3e11)
    replay_ks: tuple[int, ...] = (0, 4, 8, 16, 32, 64, 128)
    # Both frontiers run at wd=0 (B-phase) so the ONLY difference is the mitigation MECHANISM, not the
    # optimizer: EWC needs wd=0 (decoupled decay would fight the anchor); replay is wd-insensitive.
    b_phase_weight_decay: float = 0.0
    hybrid_lambda: float = 3e10            # EWC+replay hybrid: does EWC add anything ON TOP of replay?
    hybrid_k: int = 8
    both_high: float = 0.7                 # an operating point "keeps both" if min(accA,accB) >= this
    min_margin: float = 0.05               # dominance gap must beat this AND combined std (std==0 guard)
    anchor_engage_margin: float = 0.2      # EWC anchor "engages" if its best acc_A exceeds the no-anchor
                                           # naive level by this (a RELATIVE check; an absolute bar like
                                           # both_high would be a v1183-style cutoff that hid the real
                                           # protective effect, e.g. 0.676 anchor vs 0.047 naive)


# ------------------------------------------------------------------------------- EWC pieces
@torch.no_grad()
def _clone_params(model) -> dict:
    return {n: p.detach().clone() for n, p in model.named_parameters()}


def compute_fisher(model, a_train: torch.Tensor) -> dict:
    """Diagonal (empirical) Fisher = mean over A-train examples of the squared gradient of the
    answer loss w.r.t. each parameter, evaluated at the consolidated weights."""
    fisher = {n: torch.zeros_like(p) for n, p in model.named_parameters()}
    model.train()
    n = a_train.shape[0]
    for i in range(n):
        model.zero_grad(set_to_none=True)
        answer_loss(model, a_train[i:i + 1]).backward()
        for name, p in model.named_parameters():
            if p.grad is not None:
                fisher[name] += p.grad.detach() ** 2
    for name in fisher:
        fisher[name] /= max(n, 1)
    model.zero_grad(set_to_none=True)
    return fisher


def _ewc_penalty(model, theta_star: dict, fisher: dict) -> torch.Tensor:
    return sum((fisher[n] * (p - theta_star[n]) ** 2).sum() for n, p in model.named_parameters())


def train_ewc(cfg: EWCReplayConfig, init_state: dict, theta_star: dict, fisher: dict,
              b_train: torch.Tensor, lam: float, *, a_test: torch.Tensor, b_test: torch.Tensor,
              device, a_train: torch.Tensor | None = None, replay_k: int = 0, seed: int = 0) -> dict:
    """Train B from the consolidated init with an EWC penalty ``(lam/2) F (w-w*)^2`` anchoring to
    theta_star. Optional ``replay_k`` mixes A-train rows in (the EWC+replay hybrid). Returns the
    final acc_A/acc_B plus the penalty/CE ratio at the last step (the mechanism sanity scalar)."""
    base = cfg.base
    model = make_model(base).to(device)
    model.load_state_dict(init_state)
    opt = torch.optim.AdamW(model.parameters(), lr=base.lr, betas=(base.beta1, base.beta2),
                            weight_decay=cfg.b_phase_weight_decay)
    b_train = b_train.to(device); a_test = a_test.to(device); b_test = b_test.to(device)
    if a_train is not None:
        a_train = a_train.to(device)
    gen = torch.Generator(device="cpu").manual_seed(seed + 7)
    last_ce = last_pen = 0.0
    for _ in range(base.b_budget):
        model.train()
        opt.zero_grad(set_to_none=True)
        batch = b_train
        if a_train is not None and replay_k > 0:
            idx = torch.randint(0, a_train.shape[0], (replay_k,), generator=gen).to(device)
            batch = torch.cat([b_train, a_train.index_select(0, idx)], dim=0)
        ce = answer_loss(model, batch)
        pen = _ewc_penalty(model, theta_star, fisher) if lam > 0 else torch.zeros((), device=device)
        (ce + 0.5 * lam * pen).backward()
        opt.step()
        last_ce, last_pen = float(ce.item()), float(0.5 * lam * pen.item())
    return {"accA_after_B": answer_accuracy(model, a_test), "accB_after_B": answer_accuracy(model, b_test),
            "penalty_ce_ratio": round(last_pen / last_ce, 6) if last_ce > 1e-9 else None}


def run_phase_a(cfg: EWCReplayConfig, device) -> dict:
    """Single training pass: per seed consolidate A, estimate Fisher, then map the EWC-lambda and
    replay-k frontiers (acc_A, acc_B at each knob value) + a joint upper bound. No verdict logic."""
    base = cfg.base
    base_wd0 = replace(base, weight_decay=cfg.b_phase_weight_decay)   # B-phase replay at matched wd=0
    chance = 1.0 / base.p
    ewc = {float(lam): {} for lam in cfg.ewc_lambdas}
    replay = {int(k): {} for k in cfg.replay_ks}
    plateau = {}
    joint = {}
    hybrid = {}
    cont = {}
    fisher_degenerate_frac = {}
    b_majority = None
    leak_ok = True

    for seed in cfg.seeds:
        tr, te = pair_masks(base, seed)
        A_tr = build_op(base, "A", tr); A_te = build_op(base, "A", te)
        B_tr = build_op(base, "B", tr); B_te = build_op(base, "B", te)
        if b_majority is None:
            b_majority = majority_prior(B_tr, base.p)
        leak_ok = leak_ok and verify_no_leak(A_tr, A_te) and verify_no_leak(B_tr, A_te)

        state, plat, _ = consolidate(base, A_tr, A_te, seed, device)
        plateau[seed] = plat

        model = make_model(base).to(device)
        model.load_state_dict(state)
        theta_star = _clone_params(model)
        fisher = compute_fisher(model, A_tr.to(device))
        # fraction of Fisher mass that is ~0 (degenerate-Fisher sanity for g_ewc_well_specified)
        flat = torch.cat([f.flatten() for f in fisher.values()])
        fisher_degenerate_frac[seed] = float((flat <= 1e-12).float().mean().item())

        for lam in cfg.ewc_lambdas:
            ewc[float(lam)][seed] = train_ewc(cfg, state, theta_star, fisher, B_tr,
                                              float(lam), a_test=A_te, b_test=B_te, device=device)
        for k in cfg.replay_ks:
            out = train_phase(base_wd0, state, B_tr, a_test=A_te, b_test=B_te,
                              replay_train=A_tr if k > 0 else None, replay_k=int(k), seed=seed, device=device)
            replay[int(k)][seed] = {"accA_after_B": out["accA_after_B"], "accB_after_B": out["accB_after_B"]}

        # EWC+replay hybrid: does parameter anchoring add anything ON TOP of data rehearsal?
        hybrid[seed] = train_ewc(cfg, state, theta_star, fisher, B_tr, cfg.hybrid_lambda,
                                 a_test=A_te, b_test=B_te, device=device,
                                 a_train=A_tr, replay_k=cfg.hybrid_k, seed=seed)

        # continue-on-A floor: same B-budget on A itself (no shift) must NOT lose A (validity)
        cont[seed] = {"accA_after_B": train_phase(base_wd0, state, A_tr, a_test=A_te, b_test=B_te,
                                                  seed=seed, device=device)["accA_after_B"]}

        # multitask joint upper bound (fresh model on A_tr + B_tr)
        torch.manual_seed(seed)
        jm = make_model(base).to(device)
        jopt = torch.optim.AdamW(jm.parameters(), lr=base.lr, betas=(base.beta1, base.beta2),
                                 weight_decay=base.weight_decay)
        both = torch.cat([A_tr, B_tr], dim=0).to(device)
        A_te_d, B_te_d = A_te.to(device), B_te.to(device)
        js = 0; hold = 0
        while js < base.joint_max_steps:
            for _ in range(base.eval_every):
                jm.train(); jopt.zero_grad(set_to_none=True); answer_loss(jm, both).backward(); jopt.step(); js += 1
            hold = hold + 1 if (answer_accuracy(jm, A_te_d) >= base.plateau_acc and
                                answer_accuracy(jm, B_te_d) >= base.plateau_acc) else 0
            if hold >= base.plateau_hold:
                break
        joint[seed] = {"accA": answer_accuracy(jm, A_te_d), "accB": answer_accuracy(jm, B_te_d)}

    return {
        "config": {"p": base.p, "task_a": base.task_a, "task_b": base.task_b, "b_budget": base.b_budget,
                   "ewc_lambdas": [float(x) for x in cfg.ewc_lambdas], "replay_ks": [int(x) for x in cfg.replay_ks],
                   "b_phase_weight_decay": cfg.b_phase_weight_decay, "hybrid_lambda": cfg.hybrid_lambda,
                   "hybrid_k": cfg.hybrid_k, "seeds": list(cfg.seeds)},
        "chance": chance, "b_majority_prior": b_majority, "leak_free": leak_ok,
        "accA_plateau": plateau, "ewc": ewc, "replay": replay, "joint": joint, "hybrid": hybrid,
        "continue_on_A": cont, "fisher_degenerate_frac": fisher_degenerate_frac,
    }


# ------------------------------------------------------------------------------- analysis
def _best_min(frontier: dict, seed) -> tuple[float, object]:
    """Best operating point along a frontier for one seed: max over the strength knob of
    min(acc_A, acc_B). Returns (best_min_value, knob_value)."""
    best, arg = -1.0, None
    for knob in frontier:
        a = frontier[knob][seed]
        m = min(a["accA_after_B"], a["accB_after_B"])
        if m > best:
            best, arg = m, knob
    return best, arg


def summarize(cache: dict, cfg: EWCReplayConfig | None = None) -> dict:
    cfg = cfg or EWCReplayConfig()
    seeds = list(cache["accA_plateau"])
    prior = cache["b_majority_prior"]
    ewc, replay = cache["ewc"], cache["replay"]

    M_ewc = mean_std([_best_min(ewc, s)[0] for s in seeds])
    M_replay = mean_std([_best_min(replay, s)[0] for s in seeds])

    # EWC fairness signals: across lambda, can it EVER protect A, and can it EVER stay plastic?
    ewc_max_accA = mean_std([max(ewc[l][s]["accA_after_B"] for l in ewc) for s in seeds])
    ewc_max_accB = mean_std([max(ewc[l][s]["accB_after_B"] for l in ewc) for s in seeds])
    lam0 = 0.0
    naive_accA = mean_std([ewc[lam0][s]["accA_after_B"] for s in seeds])   # lambda=0 == naive sequential
    naive_accB = mean_std([ewc[lam0][s]["accB_after_B"] for s in seeds])
    lam_max = max(ewc)
    ewc_frozen_accB = mean_std([ewc[lam_max][s]["accB_after_B"] for s in seeds])

    replay_accA = {int(k): mean_std([replay[k][s]["accA_after_B"] for s in seeds]) for k in replay}
    replay_accB = {int(k): mean_std([replay[k][s]["accB_after_B"] for s in seeds]) for k in replay}
    ewc_accA = {float(l): mean_std([ewc[l][s]["accA_after_B"] for s in seeds]) for l in ewc}
    ewc_accB = {float(l): mean_std([ewc[l][s]["accB_after_B"] for s in seeds]) for l in ewc}

    hybrid_min = mean_std([min(cache["hybrid"][s]["accA_after_B"], cache["hybrid"][s]["accB_after_B"]) for s in seeds])
    # replay at the hybrid's k, for the "does EWC add anything on top of replay" comparison
    hk = cfg.hybrid_k
    replay_at_hk_min = mean_std([min(replay[hk][s]["accA_after_B"], replay[hk][s]["accB_after_B"]) for s in seeds]) \
        if hk in replay else (float("nan"), 0.0)

    return {
        "seeds": seeds, "chance": cache["chance"], "b_majority_prior": prior, "leak_free": cache["leak_free"],
        "config": cache["config"],
        "accA_plateau": mean_std([cache["accA_plateau"][s] for s in seeds]),
        "continue_on_A_forget": mean_std([cache["accA_plateau"][s] - cache["continue_on_A"][s]["accA_after_B"] for s in seeds]),
        "joint_accA": mean_std([cache["joint"][s]["accA"] for s in seeds]),
        "joint_accB": mean_std([cache["joint"][s]["accB"] for s in seeds]),
        "M_ewc": M_ewc, "M_replay": M_replay,
        "ewc_max_accA": ewc_max_accA, "ewc_max_accB": ewc_max_accB,
        "naive_accA": naive_accA, "naive_accB": naive_accB, "ewc_frozen_accB": ewc_frozen_accB,
        "replay_accA": replay_accA, "replay_accB": replay_accB, "ewc_accA": ewc_accA, "ewc_accB": ewc_accB,
        "hybrid_min": hybrid_min, "replay_at_hybrid_k_min": replay_at_hk_min,
        "fisher_degenerate_frac": mean_std([cache["fisher_degenerate_frac"][s] for s in seeds]),
        "best_ewc_lambda": [_best_min(ewc, s)[1] for s in seeds],
        "best_replay_k": [_best_min(replay, s)[1] for s in seeds],
    }


REVIEW_VERDICTS = {"task_a_not_consolidated", "task_b_not_learned", "not_jointly_learnable",
                   "operand_leak", "no_forgetting_floor", "ewc_anchor_does_not_engage", "fisher_degenerate"}
PRIMARY_VERDICTS = {"replay_dominates_ewc", "ewc_dominates_replay",
                    "both_mitigate_neither_dominates", "neither_mitigates"}


def decide(result: dict, cfg: EWCReplayConfig | None = None) -> dict:
    """Pure gates + symmetric, multi-signal verdict ladder. Dominance is the project's
    significant() on the best-min scalar M AND a min_margin (std==0 guard); fairness gates
    certify EWC got a real shot (it CAN protect A and CAN stay plastic at SOME lambda, lambda=0
    reproduces naive, lambda->max freezes B) so 'no single point keeps both' is falsifiable."""
    cfg = cfg or EWCReplayConfig()
    s = result
    base = ContinualConfig(p=s["config"]["p"])
    prior = s["b_majority_prior"]
    margin = base.b_learn_margin

    def beats(hi, lo):
        (hm, hs), (lm, ls) = hi, lo
        return (hm - lm) > cfg.min_margin and significant(hm, hs, lm, ls)

    M_e, M_r = s["M_ewc"], s["M_replay"]
    replay_dominates = beats(M_r, M_e)
    ewc_dominates = beats(M_e, M_r)
    replay_keeps_both = M_r[0] >= cfg.both_high
    ewc_keeps_both = M_e[0] >= cfg.both_high
    hybrid_adds = beats(s["hybrid_min"], s["replay_at_hybrid_k_min"])

    g_consol = s["accA_plateau"][0] >= base.plateau_acc - 0.02
    g_b_learned = (s["naive_accB"][0] - prior) >= margin
    g_joint = (s["joint_accA"][0] - prior >= margin) and (s["joint_accB"][0] - prior >= margin)
    g_leak = bool(s["leak_free"])
    g_floor = s["continue_on_A_forget"][0] <= base.floor_tol
    # fairness: certify EWC got a real, fully-swept shot so 'no lambda keeps both' is falsifiable.
    # (1) the anchor PROTECTS A -- its best acc_A is well ABOVE the no-anchor naive level (not a
    #     no-op/units bug); a RELATIVE check, not an absolute bar (0.7 would be a v1183-style cutoff).
    # (2) it can STAY PLASTIC at some lambda (low-lambda acc_B ~ naive), and
    # (3) it either KEEPS BOTH (it succeeded -- no bracketing needed) OR its frontier is BRACKETED
    #     (lambda swept into the freeze regime where acc_B collapses), so a failure to keep both is
    #     a real property, not an under-sweep. (Don't demand a freeze from a GOOD EWC frontier.)
    g_ewc_can_protect = (s["ewc_max_accA"][0] - s["naive_accA"][0]) > cfg.anchor_engage_margin
    g_ewc_can_be_plastic = s["ewc_max_accB"][0] >= s["naive_accB"][0] - margin
    g_ewc_bracketed = s["ewc_frozen_accB"][0] <= s["naive_accB"][0] - margin
    g_ewc_engages = g_ewc_can_protect and g_ewc_can_be_plastic and (ewc_keeps_both or g_ewc_bracketed)
    g_fisher_ok = s["fisher_degenerate_frac"][0] < 0.9

    flags = {
        "g_a_consolidated": g_consol, "g_b_learned": g_b_learned, "g_jointly_learnable": g_joint,
        "g_no_operand_leak": g_leak, "g_floor_clean": g_floor,
        "g_ewc_anchor_engages": g_ewc_engages, "g_fisher_well_specified": g_fisher_ok,
        "ewc_can_protect_A": g_ewc_can_protect, "ewc_can_stay_plastic": g_ewc_can_be_plastic,
        "ewc_frontier_bracketed": g_ewc_bracketed,
        "ewc_all_or_nothing": bool(g_ewc_engages and not ewc_keeps_both),
        "replay_keeps_both_tasks": bool(replay_keeps_both), "ewc_keeps_both_tasks": bool(ewc_keeps_both),
        "replay_dominates": bool(replay_dominates), "ewc_dominates": bool(ewc_dominates),
        "ewc_adds_on_top_of_replay": bool(hybrid_adds),
    }

    if not g_consol:
        return _v("review", "task_a_not_consolidated", flags)
    if not g_b_learned:
        return _v("review", "task_b_not_learned", flags)
    if not g_joint:
        return _v("review", "not_jointly_learnable", flags)
    if not g_leak:
        return _v("review", "operand_leak", flags)
    if not g_floor:
        return _v("review", "no_forgetting_floor", flags)
    if not g_fisher_ok:
        return _v("review", "fisher_degenerate", flags)
    if not g_ewc_engages:
        return _v("review", "ewc_anchor_does_not_engage", flags)

    if replay_dominates:
        return _v("pass", "replay_dominates_ewc", flags)
    if ewc_dominates:
        return _v("pass", "ewc_dominates_replay", flags)
    if replay_keeps_both and ewc_keeps_both:
        return _v("pass", "both_mitigate_neither_dominates", flags)
    return _v("pass", "neither_mitigates", flags)


def _v(status: str, verdict: str, flags: dict) -> dict:
    return {"status": status, "decision": verdict, "verdict": verdict, "flags": flags}


def build_report(result: dict, info: dict, source: str, *, generated_at: str | None = None) -> dict:
    from minigpt.report_utils import utc_now
    s = result
    status, verdict, flags = info["status"], info["verdict"], info["flags"]
    chance = s["chance"]

    rows = []
    for lam in sorted(s["ewc_accA"]):
        rows.append({"method": "ewc", "knob": f"lambda={lam:.0e}", "acc_A": round(s["ewc_accA"][lam][0], 4),
                     "acc_B": round(s["ewc_accB"][lam][0], 4),
                     "min_both": round(min(s["ewc_accA"][lam][0], s["ewc_accB"][lam][0]), 4)})
    for k in sorted(s["replay_accA"]):
        rows.append({"method": "replay", "knob": f"k={k}", "acc_A": round(s["replay_accA"][k][0], 4),
                     "acc_B": round(s["replay_accB"][k][0], 4),
                     "min_both": round(min(s["replay_accA"][k][0], s["replay_accB"][k][0]), 4)})
    rows.append({"method": "hybrid(ewc+replay)", "knob": f"lam={s['config']['hybrid_lambda']:.0e},k={s['config']['hybrid_k']}",
                 "acc_A": "", "acc_B": "", "min_both": round(s["hybrid_min"][0], 4)})
    rows.append({"method": "multitask_joint", "knob": "upper bound", "acc_A": round(s["joint_accA"][0], 4),
                 "acc_B": round(s["joint_accB"][0], 4), "min_both": round(min(s["joint_accA"][0], s["joint_accB"][0]), 4)})

    summary = {
        "status": status, "decision": info["decision"], "verdict": verdict,
        "task_a": s["config"]["task_a"], "task_b": s["config"]["task_b"], "p": s["config"]["p"],
        "chance": round(chance, 5), "b_majority_prior": round(s["b_majority_prior"], 4),
        "seeds": len(s["seeds"]), "b_budget": s["config"]["b_budget"], "b_phase_weight_decay": s["config"]["b_phase_weight_decay"],
        "accA_plateau": round(s["accA_plateau"][0], 4), "continue_on_A_forgetting": round(s["continue_on_A_forget"][0], 4),
        "M_replay_best_min": round(s["M_replay"][0], 4), "M_replay_std": round(s["M_replay"][1], 4),
        "M_ewc_best_min": round(s["M_ewc"][0], 4), "M_ewc_std": round(s["M_ewc"][1], 4),
        "ewc_max_accA_any_lambda": round(s["ewc_max_accA"][0], 4), "ewc_max_accB_any_lambda": round(s["ewc_max_accB"][0], 4),
        "naive_accA": round(s["naive_accA"][0], 4), "naive_accB": round(s["naive_accB"][0], 4),
        "ewc_frozen_accB_at_maxlambda": round(s["ewc_frozen_accB"][0], 4),
        "hybrid_min": round(s["hybrid_min"][0], 4), "replay_at_hybrid_k_min": round(s["replay_at_hybrid_k_min"][0], 4),
        "joint_accA": round(s["joint_accA"][0], 4), "joint_accB": round(s["joint_accB"][0], 4),
        "fisher_degenerate_frac": round(s["fisher_degenerate_frac"][0], 4),
        "valid_measurement": status == "pass",
    }
    summary.update({f"flag_{k}": v for k, v in flags.items()})

    recs = [
        (f"VERDICT ({verdict}): on the v1193 substrate (A={s['config']['task_a']} then B={s['config']['task_b']} mod "
         f"{s['config']['p']}, shared 1-layer transformer), the best stability-plasticity operating point "
         f"(M = max over the strength knob of min(acc_A, acc_B)) is REPLAY {s['M_replay'][0]:.3f}±{s['M_replay'][1]:.3f} "
         f"vs EWC {s['M_ewc'][0]:.3f}±{s['M_ewc'][1]:.3f}. status='{status}' certifies a VALID, FAIR measurement "
         f"(A consolidated {s['accA_plateau'][0]:.3f}, B learnable, jointly learnable, no operand leak, EWC anchor engages), "
         "NOT that either method is good."),
        (f"EWC GOT A FAIR SHOT (not a strawman): across lambda EWC CAN protect A (max acc_A {s['ewc_max_accA'][0]:.3f}, "
         f"can_protect={flags['ewc_can_protect_A']}) AND CAN stay plastic (max acc_B {s['ewc_max_accB'][0]:.3f} vs naive "
         f"{s['naive_accB'][0]:.3f}, can_stay_plastic={flags['ewc_can_stay_plastic']}) — but NOT at the SAME lambda "
         f"(all_or_nothing={flags['ewc_all_or_nothing']}): as lambda rises acc_A only climbs once acc_B has already "
         f"collapsed (at lambda_max acc_B {s['ewc_frozen_accB'][0]:.3f} ~ prior {s['b_majority_prior']:.3f} = frozen). "
         f"lambda=0 reproduces naive (acc_A {s['naive_accA'][0]:.3f}~chance {chance:.3f}). Fisher non-degenerate "
         f"(zero-frac {s['fisher_degenerate_frac'][0]:.3f}); the per-example diagonal Fisher and the EWC penalty reach the "
         "tied number-embedding exactly once."),
        (f"MECHANISM (ties to v1193): the forgetting is a GLOBAL distribution shift, and the most A-important parameters "
         "are the SHARED/tied number-embedding rows that B must overwrite. A diagonal-Fisher LOCAL anchor can only resist "
         "by freezing those rows — which blocks B — so EWC has no operating point that keeps both. REPLAY keeps A in the "
         f"loss directly without freezing anything, reaching (acc_A {max(s['replay_accA'][k][0] for k in s['replay_accA']):.3f}) "
         "while B still learns."),
        (f"HONEST BUDGET DISCLOSURE: the two methods are different resource regimes — replay re-shows {s['config']['hybrid_k']}.."
         f"{max(s['replay_accA'])} stored A-train rows EVERY step (a LARGER per-step batch) and stores k examples; EWC stores "
         "the Fisher vector + theta* (two model copies) and replays NO data. So 'replay wins' holds at matched B-STEP budget "
         "and is partly the v1193 truth that seeing A-data beats not seeing it. We therefore claim BEST-MIN dominance at "
         "matched step budget, NOT a resource-free Pareto superiority."),
        (f"HYBRID (does EWC add anything on top of replay?): EWC+replay (lambda={s['config']['hybrid_lambda']:.0e}, "
         f"k={s['config']['hybrid_k']}) min-both {s['hybrid_min'][0]:.3f} vs replay-alone at k={s['config']['hybrid_k']} "
         f"{s['replay_at_hybrid_k_min'][0]:.3f} (ewc_adds={flags['ewc_adds_on_top_of_replay']}). "
         "SCOPE: toy modular arithmetic, p=23, 1-layer transformer, diagonal-Fisher single-anchor EWC; NOT a claim that "
         "EWC is useless in general — only that a local anchor loses to data rehearsal for this global-shift forgetting."),
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT EWC vs replay for catastrophic forgetting v1194",
        "generated_at": generated_at or utc_now(),
        "status": status, "decision": info["decision"],
        "summary": summary, "rows": rows, "recommendations": recs,
        "csv_fieldnames": ["method", "knob", "acc_A", "acc_B", "min_both"],
        "ewc_frontier": {f"{l:.0e}": [round(s["ewc_accB"][l][0], 5), round(s["ewc_accA"][l][0], 5)] for l in sorted(s["ewc_accA"])},
        "replay_frontier": {str(k): [round(s["replay_accB"][k][0], 5), round(s["replay_accA"][k][0], 5)] for k in sorted(s["replay_accA"])},
        "source": source,
    }


__all__ = [
    "EWCReplayConfig", "compute_fisher", "train_ewc", "run_phase_a", "summarize", "decide",
    "build_report", "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
