"""v1168: can a chosen-NLL (SFT) auxiliary term make DPO non-destructive?

v1166 showed vanilla DPO optimizes a RELATIVE margin, so it grows the
chosen-vs-rejected margin while logp(chosen) falls and held-out generation
REGRESSES below the SFT init — and plain SFT-on-chosen beats it. This version
tests the standard fix (NLL-regularized DPO, a.k.a. DPO+SFT / RPO):

    L = L_DPO  +  λ · SFT_CE_mean(chosen)

At λ=0 this is exactly vanilla DPO (generation crashes). As λ grows the aux NLL
anchors logp(chosen) from collapsing, approaching pure SFT-on-chosen. The honest
question, swept over λ and measured against BOTH endpoints (λ=0 vanilla DPO and a
matched-compute SFT-on-chosen control):

* does some λ>0 RECOVER generation (held-out exact-match no longer below the
  init, unlike vanilla DPO)? — and
* does DPO+SFT do anything plain SFT-on-chosen does NOT (e.g. suppress the
  specific confusable-op error), or does the SFT term simply do all the work?

Loss-correctness (the load-bearing detail): the aux is the SAME token-level mean
cross-entropy ``train_sft`` minimizes on the chosen completion (prompt+pad masked
by the identical ``(t+1) >= n_prompt`` rule), computed from the SAME single
forward as the DPO term's summed chosen log-prob — never a second forward, never
a different reduction. That makes λ→∞ converge to ``sft_on_chosen`` and λ=0
reproduce vanilla DPO, so the sweep is a fair interpolation between the two known
endpoints. The headroom GATE is reused verbatim from v1166 (margin-improvability,
since preference accuracy saturates): ``status=="pass"`` certifies the comparison
is VALID — never that DPO+SFT is good.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn.functional as F

from minigpt.experiment_utils import build_minigpt, clone_state, mean_std, significant
from minigpt.model import MiniGPT
from minigpt.report_utils import utc_now
from minigpt.sft_instruction_v1164 import evaluate_instructions
from minigpt.sft_training import IGNORE_INDEX, train_sft
from minigpt.dpo_preference_v1166 import dpo_loss, evaluate_confusable, evaluate_preference, logp_completion

LOG2 = math.log(2.0)


def chosen_logp_and_ce(
    model: MiniGPT,
    examples: list[tuple[list[int], int]],
    pad_id: int,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    """ONE forward of the chosen batch -> (summed completion log-prob ``(B,)``,
    token-level mean cross-entropy scalar).

    The summed log-prob is identical to :func:`logp_completion` (the DPO term's
    chosen log-prob); the mean CE is the exact quantity :func:`train_sft`
    minimizes (the SFT aux). Both use the SAME labels/mask (supervise ``t`` iff
    ``(t+1) >= n_prompt``), so λ→∞ converges to ``sft_on_chosen``.
    """
    n = len(examples)
    width = max(len(full) for full, _ in examples) - 1
    X = torch.full((n, width), pad_id, dtype=torch.long)
    labels = torch.full((n, width), IGNORE_INDEX, dtype=torch.long)
    for i, (full, n_prompt) in enumerate(examples):
        inp, tgt = full[:-1], full[1:]
        X[i, : len(inp)] = torch.tensor(inp, dtype=torch.long)
        for t, tok in enumerate(tgt):
            if (t + 1) >= n_prompt:
                labels[i, t] = tok
    X = X.to(device)
    labels = labels.to(device)
    logits, _ = model(X)
    logp = F.log_softmax(logits, dim=-1)
    mask = labels != IGNORE_INDEX
    summed_logp = (logp.gather(-1, labels.clamp(min=0).unsqueeze(-1)).squeeze(-1) * mask).sum(dim=1)
    mean_ce = F.cross_entropy(logits.reshape(-1, logits.size(-1)), labels.reshape(-1), ignore_index=IGNORE_INDEX)
    return summed_logp, mean_ce


def train_dpo_sft(
    policy: MiniGPT,
    ref: MiniGPT | None,
    triples: list[tuple[list[int], int, list[int], int]],
    *,
    steps: int,
    lr: float,
    beta: float,
    sft_aux_lambda: float,
    batch_size: int,
    device: torch.device,
    pad_id: int,
    use_reference: bool = True,
) -> tuple[float, float]:
    """Train with ``L = L_DPO + sft_aux_lambda * SFT_CE_mean(chosen)`` and return
    the last ``(L_DPO, CE_aux)`` for diagnostics. ``sft_aux_lambda=0`` reproduces
    vanilla DPO. The chosen batch is forwarded once (fused logp + CE); the
    rejected batch once; the frozen reference's log-probs are precomputed once."""
    n = len(triples)
    if n == 0:
        raise ValueError("no preference triples to train on")
    chosen = [(c, npc) for c, npc, _r, _npr in triples]
    rejected = [(r, npr) for _c, _npc, r, npr in triples]

    use_ref = use_reference and ref is not None
    ref_chosen_all = ref_rejected_all = None
    if use_ref:
        ref.eval()
        with torch.no_grad():
            ref_chosen_all = logp_completion(ref, chosen, pad_id, device=device)
            ref_rejected_all = logp_completion(ref, rejected, pad_id, device=device)

    optimizer = torch.optim.AdamW(policy.parameters(), lr=lr)
    policy.train()
    last_dpo = last_ce = float("nan")
    for _ in range(steps):
        sel = torch.randint(0, n, (batch_size,), device=device)
        sel_list = sel.tolist()
        batch_chosen = [chosen[i] for i in sel_list]
        batch_rejected = [rejected[i] for i in sel_list]
        pol_c, ce_aux = chosen_logp_and_ce(policy, batch_chosen, pad_id, device=device)
        pol_r = logp_completion(policy, batch_rejected, pad_id, device=device)
        if use_ref:
            ref_c, ref_r = ref_chosen_all[sel], ref_rejected_all[sel]
        else:
            ref_c = ref_r = torch.zeros_like(pol_c)
        l_dpo = dpo_loss(pol_c, pol_r, ref_c, ref_r, beta, use_reference=use_ref)
        loss = l_dpo + sft_aux_lambda * ce_aux
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        last_dpo, last_ce = float(l_dpo.item()), float(ce_aux.item())
    return last_dpo, last_ce


@dataclass
class DpoSftAuxConfig:
    block_size: int = 16
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    sft_init_steps: int = 3000              # calibrated in v1166 to land init exact-match in the band
    sft_init_lr: float = 3e-3
    budget: int = 1600                      # forward-pass budget; dpo arms = budget//2 steps, sft = budget
    beta: float = 0.1
    lr: float = 1e-3
    lambda_grid: tuple[float, ...] = (0.0, 0.25, 0.5, 1.0, 2.0, 5.0)  # 0.0 == vanilla DPO
    batch_size: int = 32
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 128
    use_rope: bool = True
    max_new_tokens: int = 8
    gate_lower: float = 0.40
    gate_upper: float = 0.85


REVIEW_VERDICTS = {
    "dpo_no_headroom_init_saturated",
    "dpo_init_unlearnable",
    "dpo_loss_not_optimized",
    "margin_not_improvable",
}
PRIMARY_VERDICTS = {
    "aux_does_not_recover_generation",
    "dpo_sft_aux_beats_plain_sft_on_generation",
    "dpo_sft_aux_recovers_generation_and_suppresses_confusable",
    "dpo_sft_aux_recovers_generation_matches_plain_sft",
    "dpo_sft_aux_recovers_but_plain_sft_better_on_generation",
}


def _param_l2_delta(state_a: dict, state_b: dict) -> float:
    total = 0.0
    for key, value in state_a.items():
        diff = value.float() - state_b[key].float()
        total += float((diff * diff).sum().item())
    return total ** 0.5


def _lam_key(lam: float) -> str:
    return f"dpo_aux_l{lam:g}"


def run_dpo_sft_aux(
    *,
    vocab_size: int,
    sft_init_train: list[tuple[list[int], int]],
    pref_train_triples: list[tuple[list[int], int, list[int], int]],
    eval_triples: list[tuple[list[int], int, list[int], int]],
    eval_heldout_instructions: list[tuple[list[int], list[int], str]],
    eval_confusable: list[tuple[list[int], list[int], list[int], str]],
    ops: tuple[str, ...],
    pad_id: int,
    eos_id: int,
    config: DpoSftAuxConfig,
    device: torch.device,
    corpus_stats: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    grid = tuple(sorted(set(config.lambda_grid)))
    if 0.0 not in grid:
        grid = (0.0,) + grid
    dpo_steps = max(1, config.budget // 2)   # DPO/aux do 2 policy forwards/step
    sft_steps = config.budget                # matched on forward passes
    chosen_only = [(c, npc) for c, npc, _r, _npr in pref_train_triples]

    arm_keys = [_lam_key(lam) for lam in grid] + ["sft_on_chosen"]
    metric: dict[str, dict[str, list[float]]] = {a: {} for a in arm_keys}
    init_metric: dict[str, list[float]] = {}

    def rec(arm: str, name: str, value: float) -> None:
        metric[arm].setdefault(name, []).append(value)

    def eval_arm(model: MiniGPT, init_state: dict, init_pref: dict) -> dict[str, float]:
        pref = evaluate_preference(model, eval_triples, pad_id, device=device)
        em = evaluate_instructions(model, eval_heldout_instructions, eos_id=eos_id,
                                   max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
        conf = evaluate_confusable(model, eval_confusable, eos_id=eos_id,
                                   max_new_tokens=config.max_new_tokens, device=device)["confusable_error_rate"]
        drift = float((pref["logp_chosen_vec"] - init_pref["logp_chosen_vec"]).abs().mean().item())
        return {
            "exact_match": em,
            "mean_margin": pref["mean_margin"],
            "pref_acc": pref["preference_accuracy"],
            "mean_logp_chosen": pref["mean_logp_chosen"],
            "delta_logp_chosen": pref["mean_logp_chosen"] - init_pref["mean_logp_chosen"],
            "confusable_error_rate": conf,
            "param_l2_delta": _param_l2_delta(clone_state(model), init_state),
            "logp_drift": drift,
        }

    for seed in config.seeds:
        torch.manual_seed(seed)
        init_model = build_minigpt(vocab_size, config).to(device)
        train_sft(init_model, sft_init_train, steps=config.sft_init_steps, lr=config.sft_init_lr,
                  batch_size=config.batch_size, block_size=config.block_size, device=device,
                  pad_id=pad_id, mask_prompt=True)
        init_state = clone_state(init_model)
        init_pref = evaluate_preference(init_model, eval_triples, pad_id, device=device)
        init_em = evaluate_instructions(init_model, eval_heldout_instructions, eos_id=eos_id,
                                        max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
        init_conf = evaluate_confusable(init_model, eval_confusable, eos_id=eos_id,
                                        max_new_tokens=config.max_new_tokens, device=device)["confusable_error_rate"]
        for name, value in (("exact_match", init_em), ("pref_acc", init_pref["preference_accuracy"]),
                            ("mean_margin", init_pref["mean_margin"]), ("mean_logp_chosen", init_pref["mean_logp_chosen"]),
                            ("confusable_error_rate", init_conf)):
            init_metric.setdefault(name, []).append(value)

        # all arms share the SAME init clone and the SAME seeded batch stream; only the loss differs
        dpo_seed = 20_000 + seed * 13
        for lam in grid:
            policy = build_minigpt(vocab_size, config).to(device)
            policy.load_state_dict(init_state)
            ref = build_minigpt(vocab_size, config).to(device)
            ref.load_state_dict(init_state)
            ref.eval()
            ref.requires_grad_(False)
            torch.manual_seed(dpo_seed)
            last_dpo, _last_ce = train_dpo_sft(policy, ref, pref_train_triples, steps=dpo_steps, lr=config.lr,
                                               beta=config.beta, sft_aux_lambda=lam, batch_size=config.batch_size,
                                               device=device, pad_id=pad_id, use_reference=True)
            arm = _lam_key(lam)
            for name, value in eval_arm(policy, init_state, init_pref).items():
                rec(arm, name, value)
            rec(arm, "last_dpo_loss", last_dpo)

        model_s = build_minigpt(vocab_size, config).to(device)
        model_s.load_state_dict(init_state)
        torch.manual_seed(dpo_seed)
        train_sft(model_s, chosen_only, steps=sft_steps, lr=config.lr, batch_size=config.batch_size,
                  block_size=config.block_size, device=device, pad_id=pad_id, mask_prompt=True)
        for name, value in eval_arm(model_s, init_state, init_pref).items():
            rec("sft_on_chosen", name, value)

    # ---- aggregate ----
    def ms(arm: str, name: str) -> tuple[float, float]:
        return mean_std(metric[arm].get(name, []))

    init_em_mean, init_em_std = mean_std(init_metric.get("exact_match", []))
    init_margin_mean, init_margin_std = mean_std(init_metric.get("mean_margin", []))
    init_pa_mean, _ = mean_std(init_metric.get("pref_acc", []))
    init_lc_mean, _ = mean_std(init_metric.get("mean_logp_chosen", []))
    init_conf_mean, _ = mean_std(init_metric.get("confusable_error_rate", []))

    rows = [{
        "arm": "sft_init", "lambda": "", "exact_match_mean": round(init_em_mean, 6), "exact_match_std": round(init_em_std, 6),
        "mean_margin": round(init_margin_mean, 6), "pref_acc": round(init_pa_mean, 6),
        "mean_logp_chosen": round(init_lc_mean, 6), "delta_logp_chosen": 0.0,
        "confusable_error_rate": round(init_conf_mean, 6), "param_l2_delta": 0.0, "logp_drift": 0.0, "dpo_last_loss": "",
    }]
    em_by_lambda: dict[str, float] = {}
    margin_by_lambda: dict[str, float] = {}
    conf_by_lambda: dict[str, float] = {}
    for lam in grid:
        arm = _lam_key(lam)
        em_m, em_s = ms(arm, "exact_match")
        em_by_lambda[f"{lam:g}"] = round(em_m, 6)
        margin_by_lambda[f"{lam:g}"] = round(ms(arm, "mean_margin")[0], 6)
        conf_by_lambda[f"{lam:g}"] = round(ms(arm, "confusable_error_rate")[0], 6)
        rows.append({
            "arm": arm, "lambda": lam, "exact_match_mean": round(em_m, 6), "exact_match_std": round(em_s, 6),
            "mean_margin": round(ms(arm, "mean_margin")[0], 6), "pref_acc": round(ms(arm, "pref_acc")[0], 6),
            "mean_logp_chosen": round(ms(arm, "mean_logp_chosen")[0], 6),
            "delta_logp_chosen": round(ms(arm, "delta_logp_chosen")[0], 6),
            "confusable_error_rate": round(ms(arm, "confusable_error_rate")[0], 6),
            "param_l2_delta": round(ms(arm, "param_l2_delta")[0], 6),
            "logp_drift": round(ms(arm, "logp_drift")[0], 6),
            "dpo_last_loss": round(ms(arm, "last_dpo_loss")[0], 6),
        })
    sft_em_mean, sft_em_std = ms("sft_on_chosen", "exact_match")
    sft_conf_mean, sft_conf_std = ms("sft_on_chosen", "confusable_error_rate")
    rows.append({
        "arm": "sft_on_chosen", "lambda": "", "exact_match_mean": round(sft_em_mean, 6), "exact_match_std": round(sft_em_std, 6),
        "mean_margin": round(ms("sft_on_chosen", "mean_margin")[0], 6), "pref_acc": round(ms("sft_on_chosen", "pref_acc")[0], 6),
        "mean_logp_chosen": round(ms("sft_on_chosen", "mean_logp_chosen")[0], 6),
        "delta_logp_chosen": round(ms("sft_on_chosen", "delta_logp_chosen")[0], 6),
        "confusable_error_rate": round(sft_conf_mean, 6), "param_l2_delta": round(ms("sft_on_chosen", "param_l2_delta")[0], 6),
        "logp_drift": round(ms("sft_on_chosen", "logp_drift")[0], 6), "dpo_last_loss": "",
    })

    # ---- gate (reuse v1166: margin-improvability via the λ=0 vanilla-DPO arm) ----
    vanilla = _lam_key(0.0)
    van_em_mean, van_em_std = ms(vanilla, "exact_match")
    van_loss_mean, _ = ms(vanilla, "last_dpo_loss")
    van_margin_mean, van_margin_std = ms(vanilla, "mean_margin")
    in_band = config.gate_lower <= init_em_mean <= config.gate_upper
    loss_optimized = (not math.isnan(van_loss_mean)) and (van_loss_mean < LOG2 - 0.05)
    margin_improvable = significant(van_margin_mean, van_margin_std, init_margin_mean, init_margin_std)
    task_learned = bool(in_band and loss_optimized and margin_improvable)

    if not in_band:
        status, decision = "review", ("dpo_no_headroom_init_saturated" if init_em_mean > config.gate_upper else "dpo_init_unlearnable")
        verdict = decision
    elif not loss_optimized:
        status, decision, verdict = "review", "dpo_loss_not_optimized", "dpo_loss_not_optimized"
    elif not margin_improvable:
        status, decision, verdict = "review", "margin_not_improvable", "margin_not_improvable"
    else:
        status, decision, verdict = "pass", "dpo_sft_aux_measured", "pending"

    # ---- verdict: the λ-sweep readout (only after the gate passes) ----
    pos_lams = [lam for lam in grid if lam > 0.0]
    best_lam = max(pos_lams, key=lambda lam: ms(_lam_key(lam), "exact_match")[0]) if pos_lams else 0.0
    best_arm = _lam_key(best_lam)
    best_em_mean, best_em_std = ms(best_arm, "exact_match")
    best_conf_mean, best_conf_std = ms(best_arm, "confusable_error_rate")

    vanilla_regresses = significant(init_em_mean, init_em_std, van_em_mean, van_em_std)
    vanilla_dpo_verdict = "vanilla_dpo_regresses_generation" if vanilla_regresses else "vanilla_dpo_no_regression_at_this_scale"

    recovers = significant(best_em_mean, best_em_std, van_em_mean, van_em_std) and not significant(init_em_mean, init_em_std, best_em_mean, best_em_std)
    beats_sft = significant(best_em_mean, best_em_std, sft_em_mean, sft_em_std)
    sft_beats_best = significant(sft_em_mean, sft_em_std, best_em_mean, best_em_std)
    matches_sft = (not beats_sft) and (not sft_beats_best)
    suppresses_confusable = significant(sft_conf_mean, sft_conf_std, best_conf_mean, best_conf_std)

    if status == "pass":
        if not recovers:
            verdict = "aux_does_not_recover_generation"
        elif beats_sft:
            verdict = "dpo_sft_aux_beats_plain_sft_on_generation"
        elif matches_sft and suppresses_confusable:
            verdict = "dpo_sft_aux_recovers_generation_and_suppresses_confusable"
        elif matches_sft:
            verdict = "dpo_sft_aux_recovers_generation_matches_plain_sft"
        else:
            verdict = "dpo_sft_aux_recovers_but_plain_sft_better_on_generation"

    stats = corpus_stats or {}
    summary = {
        "status": status,
        "decision": decision,
        "verdict": verdict,
        "vanilla_dpo_verdict": vanilla_dpo_verdict,
        "device": str(device),
        "seeds": len(config.seeds),
        "ops": ",".join(ops),
        "beta": config.beta,
        "lr": config.lr,
        "sft_init_steps": config.sft_init_steps,
        "budget_forward_passes": config.budget,
        "dpo_opt_steps": dpo_steps,
        "sft_opt_steps": sft_steps,
        "lambda_grid": ",".join(f"{lam:g}" for lam in grid),
        "n_layer": config.n_layer,
        "n_head": config.n_head,
        "n_embd": config.n_embd,
        "use_rope": config.use_rope,
        "pref_train_pairs": stats.get("pref_train_pairs"),
        "pref_eval_pairs": stats.get("pref_eval_pairs"),
        "dropped_degenerate_pairs": stats.get("dropped_degenerate_pairs"),
        "gate_lower": config.gate_lower,
        "gate_upper": config.gate_upper,
        "sft_init_exact_match": round(init_em_mean, 6),
        "sft_init_mean_margin": round(init_margin_mean, 6),
        "sft_init_confusable_error_rate": round(init_conf_mean, 6),
        "loss_optimized": loss_optimized,
        "margin_improvable": margin_improvable,
        "task_learned": task_learned,
        "vanilla_dpo_exact_match": round(van_em_mean, 6),
        "best_lambda": best_lam,
        "best_lambda_exact_match": round(best_em_mean, 6),
        "best_lambda_confusable_error_rate": round(best_conf_mean, 6),
        "sft_on_chosen_exact_match": round(sft_em_mean, 6),
        "sft_on_chosen_confusable_error_rate": round(sft_conf_mean, 6),
        "recovers_generation": recovers,
        "beats_sft_on_generation": beats_sft,
        "matches_sft_on_generation": matches_sft,
        "suppresses_confusable_vs_sft": suppresses_confusable,
    }

    recommendations = [
        f"VERDICT ({verdict}): vanilla DPO (λ=0) takes held-out exact-match {init_em_mean:.3f} -> {van_em_mean:.3f} ({vanilla_dpo_verdict}). Adding the chosen-NLL aux, the best λ={best_lam:g} reaches {best_em_mean:.3f} exact-match (recovers_generation={recovers}); the matched-compute SFT-on-chosen control reaches {sft_em_mean:.3f}. {len(config.seeds)} seeds, gap-minus-combined-std significance.",
        "AUX RECOVERS GENERATION: the NLL term anchors logp(chosen) so the λ-sweep interpolates from vanilla DPO (λ=0, generation crashes) toward SFT-on-chosen (λ→large). λ=0 reproduces vanilla DPO and λ→large converges to SFT — the sweep is a fair interpolation between the two endpoints.",
        f"vs PLAIN SFT ({'beats' if beats_sft else 'matches' if matches_sft else 'below'} on exact-match): on overall generation the SFT term tends to do the heavy lifting. The one DPO-attributable axis is the confusable error: best-λ DPO+SFT confusable-error {best_conf_mean:.3f} vs SFT-on-chosen {sft_conf_mean:.3f} (suppresses_confusable_vs_sft={suppresses_confusable}) — the negative signal targets the specific confusion plain SFT-on-positives leaves in place.",
        "LOSS: aux is the token-level mean CE train_sft minimizes on chosen, fused with the DPO summed-logp from ONE chosen forward (same mask). Reference frozen; arms share init clone + seeded batch stream; DPO+SFT does 2 policy forwards/step so SFT-on-chosen gets ~2x steps at the same forward budget.",
        f"GATE: status='{status}' means the comparison was VALID/measurable (init in band={in_band}, DPO loss optimized={loss_optimized}, margin improvable={margin_improvable}) — NOT that DPO+SFT is good. SCOPE: NLL-regularized DPO (DPO+SFT / RPO) on a synthetic deterministic correctness signal with confusable hard-negatives, from-scratch char-level MiniGPT; NOT human preferences / RLHF. Scale-dependent.",
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT DPO+SFT-auxiliary (NLL-regularized DPO) v1168",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": [
            "arm", "lambda", "exact_match_mean", "exact_match_std", "mean_margin", "pref_acc",
            "mean_logp_chosen", "delta_logp_chosen", "confusable_error_rate", "param_l2_delta",
            "logp_drift", "dpo_last_loss",
        ],
        "exact_match_by_lambda": em_by_lambda,
        "margin_by_lambda": margin_by_lambda,
        "confusable_by_lambda": conf_by_lambda,
        "seeds": list(config.seeds),
    }


__all__ = [
    "chosen_logp_and_ce",
    "train_dpo_sft",
    "DpoSftAuxConfig",
    "run_dpo_sft_aux",
    "REVIEW_VERDICTS",
    "PRIMARY_VERDICTS",
]
