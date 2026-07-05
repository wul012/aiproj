"""Pure verdict logic for the v1195 task-similarity experiment."""

from __future__ import annotations

import math
from typing import Any

from minigpt.experiment_utils import significant
from minigpt.similarity_v1195_stats import (
    _interp,
    _isotonic_decreasing,
    _ols2,
    spearman,
    spearman_perm_p,
)


REVIEW_VERDICTS = {
    "task_a_not_consolidated",
    "no_forgetting_floor",
    "operand_leak",
    "not_jointly_learnable",
    "too_few_learnable_curve_points",
    "underpowered_type_contrast",
}
PRIMARY_VERDICTS = {
    "forgetting_governed_by_output_overlap",
    "overlap_grades_forgetting_with_residual_structure",
    "forgetting_tracks_task_type",
    "no_overlap_dependence",
}


def decide_similarity(result: dict, cfg: Any) -> dict:
    """Apply the pre-registered, margin-aware v1195 verdict ladder."""
    st = result["stats"]

    def beats(more, less):
        (mm, ms), (lm, ls) = more, less
        return (mm - lm) > cfg.min_reduction and significant(mm, ms, lm, ls)

    g_consol = result["per_seed_plateau_ok"] and result["plateau"][0] >= cfg.base.plateau_acc - 0.02
    g_floor = result["continue_on_A_forget"][0] <= cfg.floor_tol
    g_leak = bool(result["leak_free"])
    prior = st["type:mul"]["prior"] if "type:mul" in st else next(iter(st.values()))["prior"]
    g_joint = (
        (result["joint_accA"][0] - prior) >= cfg.b_learn_margin
        and (result["joint_accB"][0] - prior) >= cfg.b_learn_margin
    )

    mix = [st[k] for k in result["mix_keys"]]
    mix_learned = [m for m in mix if m["learned"]]
    mix_curve = [m for m in mix_learned if m["overlap"][0] < 0.999]
    g_enough = len(mix_curve) >= 4

    indep_type = [st[k] for k in ("type:add_offset", "type:linear", "type:rand") if k in st]
    indep_learned = [t for t in indep_type if t["learned"]]
    degenerate_zero_variance = any(m["forget"][1] == 0.0 for m in mix_learned)

    ov = [m["overlap"][0] for m in mix_curve]
    fg = [m["forget"][0] for m in mix_curve]
    rho = spearman(ov, fg) if len(mix_curve) >= 3 else float("nan")
    rho_p = spearman_perm_p(ov, fg) if len(mix_curve) >= 3 else float("nan")
    if mix_curve:
        lo = min(mix_curve, key=lambda m: m["overlap"][0])
        hi = max(mix_curve, key=lambda m: m["overlap"][0])
        span = lo["forget"][0] - hi["forget"][0]
        c1_slope = (
            rho <= cfg.spearman_floor
            and span >= cfg.c1_min_range
            and beats(lo["forget"], hi["forget"])
        )
    else:
        span, c1_slope = 0.0, False

    allp = mix_curve + indep_learned
    if len(allp) >= 4:
        y = [m["forget"][0] for m in allp]
        xo = [m["overlap"][0] for m in allp]
        xb = [
            m["accB_train_conflict"][0]
            if not math.isnan(m["accB_train_conflict"][0])
            else m["accB_train"][0]
            for m in allp
        ]
        xd = [m["emb_drift"][0] for m in allp]
        b_ov_accB, b_accB, _ = _ols2(y, xo, xb)
        b_ov_drift, b_drift, _ = _ols2(y, xo, xd)
        overlap_survives = (
            b_ov_accB < 0
            and abs(b_ov_accB) >= abs(b_accB)
            and b_ov_drift < 0
            and abs(b_ov_drift) >= abs(b_drift)
        )
    else:
        b_ov_accB = b_accB = b_ov_drift = b_drift = float("nan")
        overlap_survives = False

    plat_m = result["plateau"][0]
    sl_devs = [m["forget"][0] - (1.0 - m["overlap"][0]) * plat_m for m in mix_curve]
    superlinear = (sum(sl_devs) / len(sl_devs)) >= cfg.superlinear_margin if sl_devs else False

    ao, mu, asame = st.get("type:add_offset"), st.get("type:mul"), st.get("type:add_same")
    have_c2 = ao is not None and mu is not None and asame is not None
    type_lowov = [
        t
        for t in (ao, mu, st.get("type:rand"))
        if t is not None and t["learned"] and t["overlap"][0] <= cfg.low_overlap_max
    ]
    combined_std_type = (
        math.sqrt(ao["forget"][1] ** 2 + mu["forget"][1] ** 2) if have_c2 else float("nan")
    )
    underpowered_type = bool(have_c2 and combined_std_type > 0.20)
    c2_equiv = bool(
        have_c2
        and ao["learned"]
        and mu["learned"]
        and abs(ao["forget"][0] - mu["forget"][0]) <= cfg.equiv_delta - combined_std_type
        and beats(ao["forget"], asame["forget"])
        and beats(mu["forget"], asame["forget"])
    )
    family_protects = bool(
        have_c2 and ao["learned"] and mu["learned"] and beats(mu["forget"], ao["forget"])
    )

    curve = (
        _isotonic_decreasing(
            [m["overlap"][0] for m in mix_curve],
            [m["forget"][0] for m in mix_curve],
        )
        if len(mix_curve) >= 2
        else []
    )
    residuals = {}
    c3_ok = bool(indep_learned) and bool(curve)
    for item in indep_learned if curve else []:
        pred = _interp(curve, item["overlap"][0])
        residual = abs(item["forget"][0] - pred)
        tolerance = max(cfg.residual_std_mult * item["forget"][1], cfg.residual_margin)
        residuals[item["key"]] = {
            "overlap": round(item["overlap"][0], 4),
            "forget": round(item["forget"][0], 4),
            "pred": round(pred, 4),
            "residual": round(residual, 4),
            "tol": round(tolerance, 4),
            "within": bool(residual <= tolerance),
        }
        c3_ok = c3_ok and residual <= tolerance

    structure_at_fixed_overlap = bool(indep_learned) and not c3_ok
    lowov_forget_spread = (
        max(t["forget"][0] for t in type_lowov) - min(t["forget"][0] for t in type_lowov)
        if len(type_lowov) >= 2
        else 0.0
    )

    flags = {
        "g_a_consolidated": bool(g_consol),
        "g_floor_clean": bool(g_floor),
        "g_no_operand_leak": bool(g_leak),
        "g_jointly_learnable": bool(g_joint),
        "g_enough_curve_points": bool(g_enough),
        "degenerate_zero_variance": bool(degenerate_zero_variance),
        "c1_monotone_slope": bool(c1_slope),
        "spearman_overlap_forget": round(rho, 4),
        "spearman_perm_p": round(rho_p, 4) if not math.isnan(rho_p) else None,
        "slope_span": round(span, 4),
        "overlap_survives_accB_and_drift": bool(overlap_survives),
        "beta_overlap_given_accB": round(b_ov_accB, 3) if not math.isnan(b_ov_accB) else None,
        "beta_accB": round(b_accB, 3) if not math.isnan(b_accB) else None,
        "beta_overlap_given_drift": round(b_ov_drift, 3) if not math.isnan(b_ov_drift) else None,
        "beta_drift": round(b_drift, 3) if not math.isnan(b_drift) else None,
        "superlinear_vs_overwrite_null": bool(superlinear),
        "mean_superlinear_excess": round(sum(sl_devs) / len(sl_devs), 4) if sl_devs else None,
        "c2_family_does_not_protect": bool(c2_equiv),
        "family_protects": bool(family_protects),
        "underpowered_type_contrast": bool(underpowered_type),
        "c3_type_points_on_curve": bool(c3_ok),
        "residuals": residuals,
        "structure_at_fixed_overlap": bool(structure_at_fixed_overlap),
        "lowov_forget_spread": round(lowov_forget_spread, 4),
        "n_mix_learned": len(mix_learned),
        "n_mix_curve": len(mix_curve),
        "n_indep_type_learned": len(indep_learned),
    }

    if not g_consol:
        return _verdict("review", "task_a_not_consolidated", flags)
    if not g_floor:
        return _verdict("review", "no_forgetting_floor", flags)
    if not g_leak:
        return _verdict("review", "operand_leak", flags)
    if not g_joint:
        return _verdict("review", "not_jointly_learnable", flags)
    if not g_enough:
        return _verdict("review", "too_few_learnable_curve_points", flags)
    if underpowered_type and not family_protects:
        return _verdict("review", "underpowered_type_contrast", flags)
    if not c1_slope:
        return _verdict("pass", "no_overlap_dependence", flags)
    if family_protects:
        return _verdict("pass", "forgetting_tracks_task_type", flags)
    if c2_equiv and c3_ok and overlap_survives:
        return _verdict("pass", "forgetting_governed_by_output_overlap", flags)
    return _verdict("pass", "overlap_grades_forgetting_with_residual_structure", flags)


def _verdict(status: str, verdict: str, flags: dict) -> dict:
    return {"status": status, "decision": verdict, "verdict": verdict, "flags": flags}


__all__ = ["PRIMARY_VERDICTS", "REVIEW_VERDICTS", "decide_similarity"]
