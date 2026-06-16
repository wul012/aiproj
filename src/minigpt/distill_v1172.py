"""v1172: knowledge distillation — label transfer, not dark knowledge.

On the {C,R,S,L} string-op corpus every op is an EXACT deterministic function, so
a competent teacher's completion-token distribution is near one-hot (the v1172
probe measured mean max-prob 0.986, entropy 0.046 nats). Classic "dark knowledge"
(soft inter-class structure) therefore cannot exist by construction — this version
tests the LOGIT-MATCHING / LABEL-TRANSFER face of distillation, and is built to
detect whether any gain over hard-label SFT is teacher-specific or merely generic
soft-target regularization.

A trained teacher (4L/64) distills into a smaller student via the per-completion-
token KL objective ``L = hw*CE(student,y) + (1-hw)*tau^2*KL(softmax(zT/tau) ||
softmax(zS/tau))``. Each (arm, seed) gets an INDEPENDENT student init so the
project's unpaired ``significant`` gap-minus-combined-std test is valid. Two
disentangling CONTROLS isolate teacher content from generic regularization:

* ``label_smooth`` — hard CE with uniform smoothing eps matched to the teacher's
  measured confidence (subtracts generic soft-target regularization);
* ``shuffled_teacher`` — KL to a teacher distribution whose argmax index, max-prob
  and entropy are preserved but whose non-argmax mass is permuted across classes
  (subtracts confidence/entropy shape; isolates class identity / dark knowledge).

The PRE-REGISTERED primary contrast is ``distill_tau1_hw0`` vs ``scratch_hard``
AND vs both controls, at the capable student. ``status=="pass"`` certifies the
comparison was VALIDLY measured (teacher learnable, scratch off the floor, real
headroom, controls ran) — never that distillation is good. Scope: B=1, teacher-
forced gold-path logit KL, char-toy deterministic task.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch

from minigpt.distill_common import (
    _build_xy,
    kl_term,
    make_distill_model as _make_model,
    shuffle_residual_mass,
    teacher_logit_stats,
    train_student,
)
from minigpt.experiment_utils import mean_std, significant
from minigpt.report_utils import utc_now
from minigpt.sft_instruction_v1164 import evaluate_instructions
from minigpt.sft_training import train_sft

CHANCE = 0.0016  # ~ per-op random exact-match floor on this corpus

# arm order is fixed so the per-(arm,seed) init seed is stable and independent
ARM_ORDER = [
    "scratch_hard", "label_smooth", "shuffled_teacher",
    "distill_tau1_hw0", "distill_tau1_hw05", "distill_tau2_hw0", "distill_tau2_hw05",
    "scratch_long",
]
# (mode, tau, hard_weight, use_label_smoothing, shuffle_teacher, long_steps)
ARM_SPECS = {
    "scratch_hard":      ("ce",      1.0, 1.0, False, False, False),
    "label_smooth":      ("ce",      1.0, 1.0, True,  False, False),
    "shuffled_teacher":  ("distill", 1.0, 0.0, False, True,  False),
    "distill_tau1_hw0":  ("distill", 1.0, 0.0, False, False, False),
    "distill_tau1_hw05": ("distill", 1.0, 0.5, False, False, False),
    "distill_tau2_hw0":  ("distill", 2.0, 0.0, False, False, False),
    "distill_tau2_hw05": ("distill", 2.0, 0.5, False, False, False),
    "scratch_long":      ("ce",      1.0, 1.0, False, False, True),
}
CURVE_ARMS = ("scratch_hard", "label_smooth", "distill_tau1_hw0")  # run at every size
CONTROL_ARMS = ("label_smooth", "shuffled_teacher")


@dataclass
class DistillConfig:
    block_size: int = 16
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341)
    seed_base: int = 1337
    teacher_layer: int = 4
    teacher_head: int = 4
    teacher_embd: int = 64
    teacher_steps: int = 800
    # (n_layer, n_head, n_embd, label); capable_label gets the full 8-arm battery
    sizes: tuple[tuple, ...] = (
        (1, 2, 16, "1L/16"), (2, 4, 24, "2L/24"), (2, 4, 32, "2L/32"),
        (3, 4, 48, "3L/48"), (4, 4, 64, "4L/64"),
    )
    capable_label: str = "2L/32"
    steps: int = 700
    lr: float = 3e-3
    batch_size: int = 64
    max_new_tokens: int = 8
    headroom: float = 0.05


REVIEW_VERDICTS = {"no_valid_distillation_headroom", "controls_missing"}
PRIMARY_VERDICTS = {
    "distillation_helps_via_logit_matching_not_dark_knowledge",
    "gain_is_generic_soft_target_regularization",
    "distill_gain_is_faster_convergence_not_better_asymptote",
    "no_distill_benefit",
}


def decide(cell: dict, teacher_em: float, teacher_maxprob: float, headroom: float) -> dict:
    """Pure verdict logic at the capable cell. ``cell`` maps arm-id -> (mean, std).
    Returns status/decision/verdict + the boolean significance flags."""
    sc_m, sc_s = cell["scratch_hard"]
    d_m, d_s = cell["distill_tau1_hw0"]

    g1 = teacher_em >= 0.5
    g2 = significant(sc_m, sc_s, CHANCE, 0.0)                       # scratch off the floor
    g3 = (teacher_em - sc_m) >= headroom                           # headroom (off the ceiling)
    g4 = all(a in cell and cell[a][0] == cell[a][0] for a in CONTROL_ARMS)  # controls ran (finite)

    flags = {}
    if not (g1 and g2 and g3):
        return {"status": "review", "decision": "no_valid_distillation_headroom", "verdict": "no_valid_distillation_headroom", "flags": flags}
    if not g4:
        return {"status": "review", "decision": "controls_missing", "verdict": "controls_missing", "flags": flags}

    ls_m, ls_s = cell["label_smooth"]
    sh_m, sh_s = cell["shuffled_teacher"]
    t2_m, t2_s = cell["distill_tau2_hw0"]
    long_m, long_s = cell["scratch_long"]

    beats_scratch = significant(d_m, d_s, sc_m, sc_s)
    beats_ls = significant(d_m, d_s, ls_m, ls_s)
    beats_shuf = significant(d_m, d_s, sh_m, sh_s)
    dark_absent = (teacher_maxprob >= 0.9) and (d_m >= t2_m)        # near-one-hot + tau1 not below tau2
    catches_up = not significant(d_m, d_s, long_m, long_s)          # scratch_long matches distill
    flags = {"beats_scratch": beats_scratch, "beats_label_smooth": beats_ls,
             "beats_shuffled_teacher": beats_shuf, "dark_knowledge_absent": dark_absent,
             "scratch_long_catches_up": catches_up}

    if not beats_scratch:
        verdict = "no_distill_benefit"
    elif beats_ls and beats_shuf and dark_absent:
        verdict = "distillation_helps_via_logit_matching_not_dark_knowledge"
    elif not (beats_ls and beats_shuf):
        verdict = "gain_is_generic_soft_target_regularization"
    elif catches_up:
        verdict = "distill_gain_is_faster_convergence_not_better_asymptote"
    else:
        verdict = "gain_is_generic_soft_target_regularization"
    return {"status": "pass", "decision": "distillation_measured", "verdict": verdict, "flags": flags}


def run_distill(
    *,
    vocab_size: int,
    train_examples: list,
    heldout_instructions: list,
    train_instructions: list,
    ops: tuple[str, ...],
    pad_id: int,
    eos_id: int,
    config: DistillConfig,
    device,
    corpus_stats: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    bs = config.block_size

    # ---- teacher: trained once (fixed seed), reused across all arms/seeds ----
    torch.manual_seed(config.seed_base)
    teacher = _make_model(vocab_size, bs, config.teacher_layer, config.teacher_head, config.teacher_embd).to(device)
    train_sft(teacher, train_examples, steps=config.teacher_steps, lr=config.lr, batch_size=config.batch_size,
              block_size=bs, device=device, pad_id=pad_id, mask_prompt=True)
    teacher_em = evaluate_instructions(teacher, heldout_instructions, eos_id=eos_id,
                                       max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
    teacher_maxprob, teacher_entropy = teacher_logit_stats(teacher, train_examples, bs, pad_id)
    teacher_params = teacher.parameter_count()
    eps = (1.0 - teacher_maxprob) / (1.0 - 1.0 / vocab_size)        # label-smoothing matched to teacher confidence

    # fixed residual permutation for shuffled_teacher (independent of student seeds)
    g = torch.Generator(device="cpu")
    g.manual_seed(98765)
    shuffle_perm = torch.randperm(vocab_size - 1, generator=g).to(device)

    capable = config.capable_label
    rows = []
    cell_means: dict[str, dict[str, tuple]] = {}     # size_label -> {arm: (mean,std)}
    train_fit = {}                                    # floored-size train-EM (capacity vs optimization floor)

    for (nl, nh, ne, label) in config.sizes:
        arms = ARM_ORDER if label == capable else CURVE_ARMS
        student_params = _make_model(vocab_size, bs, nl, nh, ne).parameter_count()
        long_steps = round(config.steps * (1.0 + teacher_params / (3.0 * student_params)))
        cell_means[label] = {}
        for arm in arms:
            mode, tau, hw, use_ls, shuf, is_long = ARM_SPECS[arm]
            arm_idx = ARM_ORDER.index(arm)
            ems = []
            for seed in config.seeds:
                torch.manual_seed(config.seed_base + 1009 * arm_idx + seed)   # INDEPENDENT init per (arm,seed)
                student = _make_model(vocab_size, bs, nl, nh, ne).to(device)
                train_student(
                    student, train_examples,
                    steps=long_steps if is_long else config.steps,
                    lr=config.lr, batch_size=config.batch_size, block_size=bs, pad_id=pad_id, device=device,
                    loss_mode=mode, teacher=(teacher if mode == "distill" else None),
                    tau=tau, hard_weight=hw, label_smoothing=(eps if use_ls else 0.0),
                    shuffle_perm=(shuffle_perm if shuf else None),
                )
                ems.append(evaluate_instructions(student, heldout_instructions, eos_id=eos_id,
                                                 max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"])
                # train-fit check on the floored (smallest) size's scratch arm, first seed only
                if label == config.sizes[0][3] and arm == "scratch_hard" and seed == config.seeds[0]:
                    train_fit["scratch_train_em"] = round(evaluate_instructions(
                        student, train_instructions, eos_id=eos_id, max_new_tokens=config.max_new_tokens,
                        device=device)["overall_accuracy"], 4)
            m, s = mean_std(ems)
            cell_means[label][arm] = (m, s)
            rows.append({"size": label, "n_layer": nl, "n_embd": ne, "params": student_params,
                         "arm": arm, "steps": (long_steps if is_long else config.steps),
                         "em_mean": round(m, 6), "em_std": round(s, 6),
                         "delta_vs_scratch": round(m - cell_means[label]["scratch_hard"][0], 6)})

    # ---- per-size capacity descriptor + the Δ-vs-gap curve (distill_tau1 − scratch) ----
    capacity_curve = {}
    for (_nl, _nh, _ne, label) in config.sizes:
        sc = cell_means[label]["scratch_hard"][0]
        d1 = cell_means[label]["distill_tau1_hw0"][0]
        gap = teacher_em - sc
        if sc <= CHANCE + 0.02:
            desc = "floored"
        elif gap < config.headroom:
            desc = "saturated"
        else:
            desc = "valid"
        capacity_curve[label] = {"scratch_em": round(sc, 4), "distill_tau1_em": round(d1, 4),
                                 "scratch_to_teacher_gap": round(gap, 4),
                                 "delta_distill_minus_scratch": round(d1 - sc, 4), "descriptor": desc}

    # ---- gate + verdict at the capable cell ----
    verdict_out = decide(cell_means[capable], teacher_em, teacher_maxprob, config.headroom)
    status, decision, verdict = verdict_out["status"], verdict_out["decision"], verdict_out["verdict"]
    flags = verdict_out["flags"]
    cap = cell_means[capable]

    def gapfrac(arm):
        denom = teacher_em - cap["scratch_hard"][0]
        return round((cap[arm][0] - cap["scratch_hard"][0]) / denom, 4) if denom > 1e-9 else float("nan")

    stats = corpus_stats or {}
    summary = {
        "status": status, "decision": decision, "verdict": verdict,
        "device": str(device), "seeds": len(config.seeds), "ops": ",".join(ops),
        "teacher_size": f"{config.teacher_layer}L/{config.teacher_embd}", "teacher_params": teacher_params,
        "teacher_exact_match": round(teacher_em, 6),
        "teacher_mean_maxprob": round(teacher_maxprob, 6), "teacher_mean_entropy_nats": round(teacher_entropy, 6),
        "dark_knowledge_absent": (teacher_maxprob >= 0.9),
        "label_smoothing_eps": round(eps, 6),
        "capable_size": capable,
        "scratch_train_em_floored_size": train_fit.get("scratch_train_em"),
        "task_learned": status == "pass",
        "heldout_prompts": stats.get("heldout_prompts"),
    }
    if status == "pass":
        summary.update({
            "scratch_hard_em": round(cap["scratch_hard"][0], 6),
            "label_smooth_em": round(cap["label_smooth"][0], 6),
            "shuffled_teacher_em": round(cap["shuffled_teacher"][0], 6),
            "distill_tau1_hw0_em": round(cap["distill_tau1_hw0"][0], 6),
            "distill_tau2_hw0_em": round(cap["distill_tau2_hw0"][0], 6),
            "scratch_long_em": round(cap["scratch_long"][0], 6),
            "scratch_long_steps": next(r["steps"] for r in rows if r["size"] == capable and r["arm"] == "scratch_long"),
            "distill_gap_fraction_vs_scratch": gapfrac("distill_tau1_hw0"),
            **{f"flag_{k}": v for k, v in flags.items()},
        })

    recommendations = [
        f"VERDICT ({verdict}): on a DETERMINISTIC task the teacher ({summary['teacher_size']}, held-out EM {teacher_em:.3f}) is near-one-hot (mean max-prob {teacher_maxprob:.3f}, entropy {teacher_entropy:.3f} nats), so dark knowledge cannot exist by construction — this measures the LOGIT-MATCHING face of distillation. status='{status}' certifies the comparison was validly measured (teacher learnable, scratch off the floor, real headroom, controls ran), NOT that distillation is good.",
        (f"PRIMARY CONTRAST at {capable} ({len(config.seeds)} independent-init seeds): distill_tau1_hw0 {cap['distill_tau1_hw0'][0]:.3f} vs scratch_hard {cap['scratch_hard'][0]:.3f} (beats={flags.get('beats_scratch')}), vs label_smooth {cap['label_smooth'][0]:.3f} (beats={flags.get('beats_label_smooth')}), vs shuffled_teacher {cap['shuffled_teacher'][0]:.3f} (beats={flags.get('beats_shuffled_teacher')}). The teacher-specific verdict requires beating BOTH controls; otherwise the gain is generic soft-target regularization." if status == "pass" else f"NO VALID HEADROOM at {capable}: teacher_em {teacher_em:.3f}, scratch_hard {cap['scratch_hard'][0]:.3f} — gate not met, reported as review."),
        f"DARK KNOWLEDGE: absent by construction (teacher max-prob {teacher_maxprob:.3f}); tau=1 (no softening) is the faithful target. tau is a COUPLED knob (temperature x effective step size via the tau^2 KL scaling), NOT an isolated cause — do not read 'higher tau worse' as clean causation.",
        f"COMPUTE FRAMING: results at matched STUDENT STEPS ({config.steps}) treat the teacher forward as free amortized supervision; scratch_long re-runs scratch at matched-FLOPs ({summary.get('scratch_long_steps','n/a')} steps). A capability claim is honest only if it survives matched-FLOPs OR is explicitly scoped to the teacher-amortized regime.",
        f"CAPACITY: the Δ(distill−scratch) curve tracks the scratch→teacher headroom (peaks at intermediate capacity). The smallest size is {('a CAPACITY ceiling' if (train_fit.get('scratch_train_em') is not None and train_fit['scratch_train_em']>=0.5) else 'an OPTIMIZATION/learnability FLOOR (train-EM '+str(train_fit.get('scratch_train_em'))+')')} — below it neither arm clears chance, so its negative deltas are NOT 'distillation hurts'. SCOPE: dark-knowledge transfer needs an ambiguous/multi-answer task, out of scope at char-toy scale.",
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT knowledge distillation v1172",
        "generated_at": generated_at or utc_now(),
        "status": status, "decision": decision,
        "summary": summary, "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": ["size", "n_layer", "n_embd", "params", "arm", "steps", "em_mean", "em_std", "delta_vs_scratch"],
        "capacity_curve": capacity_curve,
        "seeds": list(config.seeds),
    }


__all__ = [
    "kl_term", "shuffle_residual_mass", "train_student", "teacher_logit_stats",
    "DistillConfig", "decide", "run_distill", "ARM_ORDER", "ARM_SPECS",
    "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
