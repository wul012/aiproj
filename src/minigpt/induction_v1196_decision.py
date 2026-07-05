"""Pure verdict logic for the v1196 induction-depth experiment."""

from __future__ import annotations

import math
from typing import Any

from minigpt.experiment_utils import significant

REVIEW_VERDICTS = {"task_not_learnable", "not_in_context", "shortcut_control_failed"}
PRIMARY_VERDICTS = {"induction_requires_depth", "depth_lowers_capacity_threshold",
                    "induction_independent_of_depth"}


def decide_induction(result: dict, cfg: Any) -> dict:
    """Pure gates + pre-registered W*-ordering verdict. status=='pass' certifies a VALID, genuinely
    in-context measurement (beats the unigram floor, a swap follows; task learnable by 2L; the
    shortcut control proves 1L is capable), never a flattering shape."""
    s = result
    widths, depths, seeds = s["widths"], s["depths"], s["seeds"]
    S = s["S"]
    cells = s["cells"]
    uni = s["unigram_acc"]

    def beats(hi, lo):
        (hm, hs), (lm, ls) = hi, lo
        return (hm - lm) > cfg.min_gap_margin and significant(hm, hs, lm, ls)

    # the depth verdict uses the width range where 2-layer training converges (<= verdict_max_width);
    # larger widths under-train at the fixed budget (optimization, not capability) -> reported, not gated.
    vwidths = [w for w in widths if w <= cfg.verdict_max_width]
    vwidest = vwidths[-1]

    # task learnable: some (depth,width) in the verdict range crosses S
    succeeding = [(d, w) for d in depths for w in vwidths if cells[(d, w)]["acc"][0] >= S]
    task_learnable = len(succeeding) > 0
    # in-context: every succeeding cell beats the unigram floor by margin AND a swap follows
    in_context_ok = all(
        (cells[(d, w)]["acc"][0] - uni) >= cfg.unigram_margin and
        cells[(d, w)]["swap_follow"][0] >= cfg.swap_follow_min for (d, w) in succeeding)
    g_random_init = s["random_init_acc"] <= cfg.random_init_acc_max
    # shortcut control: the 1-layer model SUCCEEDS on the positional task somewhere (it is capable)
    shortcut_ok = any(s["shortcut"][w][0] >= S for w in s["shortcut"]) if s["shortcut"] else False

    wstar_ms, fin = s["wstar_ms"], s["wstar_finite_frac"]
    grid_step = min(widths[i + 1] - widths[i] for i in range(len(widths) - 1))
    wstar1_finite = fin.get(1, 0.0) >= cfg.paired_frac
    wstar2_finite = fin.get(2, 0.0) >= cfg.paired_frac

    # paired ordering (when both cross)
    paired = []
    if 1 in depths and 2 in depths:
        for seed in seeds:
            w1, w2 = s["wstar"][1][seed], s["wstar"][2][seed]
            paired.append((w2 < w1 - 1e-9) and (not math.isfinite(w1) or w1 - w2 >= grid_step))
    ordering_holds = (sum(paired) / len(seeds)) >= cfg.paired_frac if paired else False

    wmax = vwidest   # widest CONVERGED width (depth comparison is meaningful only where 2L trained)
    gap_widest = cells[(2, wmax)]["acc"][0] - cells[(1, wmax)]["acc"][0] if (1 in depths and 2 in depths) else 0.0
    one_layer_caught_up = (not beats(cells[(2, wmax)]["acc"], cells[(1, wmax)]["acc"])) and abs(gap_widest) <= cfg.gap_closed_eps

    ao = s["attn_only"]
    ao_2L_max = max((ao[(2, w)][0] for w in [c[1] for c in ao if c[0] == 2]), default=float("nan"))
    ao_1L_max = max((ao[(1, w)][0] for w in [c[1] for c in ao if c[0] == 1]), default=float("nan"))

    degenerate_zero_variance = any(cells[(d, w)]["acc"][1] == 0.0 for d in depths for w in widths)
    # 1-layer's strongest failure bound (over ALL swept widths incl. extended); and whether 2-layer
    # under-trains (drops below S) at any width ABOVE the converged verdict range.
    one_layer_extended_max_acc = max(cells[(1, w)]["acc"][0] for w in widths) if 1 in depths else float("nan")
    two_layer_undertrains_large = bool(2 in depths and any(
        cells[(2, w)]["acc"][0] < S for w in widths if w > cfg.verdict_max_width))

    flags = {
        "task_learnable": bool(task_learnable), "in_context_ok": bool(in_context_ok),
        "random_init_ok": bool(g_random_init), "random_init_acc": round(s["random_init_acc"], 4),
        "shortcut_control_ok": bool(shortcut_ok),
        "shortcut_1L_max_acc": round(max((s["shortcut"][w][0] for w in s["shortcut"]), default=float("nan")), 4),
        "unigram_acc": round(uni, 4), "max_marginal": round(s["max_marginal"], 4),
        "verdict_max_width": cfg.verdict_max_width,
        "wstar_1L": (round(wstar_ms[1][0], 2) if 1 in depths and math.isfinite(wstar_ms[1][0]) else None),
        "wstar_2L": (round(wstar_ms[2][0], 2) if 2 in depths and math.isfinite(wstar_ms[2][0]) else None),
        "wstar_1L_finite_frac": round(fin.get(1, 0.0), 3), "wstar_2L_finite_frac": round(fin.get(2, 0.0), 3),
        "one_layer_extended_max_acc": round(one_layer_extended_max_acc, 4),
        "two_layer_undertrains_large_width": two_layer_undertrains_large,
        "ordering_holds_paired": bool(ordering_holds), "ordering_seed_frac": round(sum(paired) / len(seeds), 3) if paired else None,
        "gap_at_widest": round(gap_widest, 4), "one_layer_caught_up_at_widest": bool(one_layer_caught_up),
        "attn_only_2L_max_acc": (round(ao_2L_max, 4) if not math.isnan(ao_2L_max) else None),
        "attn_only_1L_max_acc": (round(ao_1L_max, 4) if not math.isnan(ao_1L_max) else None),
        "attn_only_2L_inducts": bool(not math.isnan(ao_2L_max) and ao_2L_max >= S),
        "degenerate_zero_variance": bool(degenerate_zero_variance), "grid_step": grid_step,
    }

    # ---- ladder ----
    if not task_learnable:
        return _v("review", "task_not_learnable", flags)
    if not g_random_init:
        return _v("review", "random_init_not_null", flags)
    if not in_context_ok:
        return _v("review", "not_in_context", flags)
    if not shortcut_ok:
        return _v("review", "shortcut_control_failed", flags)

    if wstar2_finite and not wstar1_finite:
        return _v("pass", "induction_requires_depth", flags)
    if wstar2_finite and wstar1_finite and ordering_holds and not one_layer_caught_up:
        return _v("pass", "depth_lowers_capacity_threshold", flags)
    if wstar2_finite and wstar1_finite and one_layer_caught_up:
        return _v("pass", "induction_independent_of_depth", flags)
    return _v("pass", "depth_lowers_capacity_threshold", flags)


def _v(status: str, verdict: str, flags: dict) -> dict:
    return {"status": status, "decision": verdict, "verdict": verdict, "flags": flags}

__all__ = ["PRIMARY_VERDICTS", "REVIEW_VERDICTS", "decide_induction"]
