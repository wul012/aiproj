"""Pure verdict logic for the v1197 induction-circuit experiment."""

from __future__ import annotations

from typing import Any

REVIEW_VERDICTS = {"base_not_inducting", "circuit_not_classifiable", "mean_zero_disagree", "tau_fragile"}
PRIMARY_VERDICTS = {"circuit_necessary_specific_composed_and_redundant",
                    "circuit_necessary_specific_composed_concentrated",
                    "circuit_necessary_specific_composed_redundancy_unassessed",
                    "circuit_necessary_specific_not_composed", "circuit_not_clean"}


def decide_induction_circuit(result: dict, cfg: Any) -> dict:
    p = result["primary"]
    flags = {
        "base_acc": round(p["base_acc"][0], 4), "unigram_acc": round(p["unigram"], 4),
        "n_trained": p["n_trained"], "n_all": p["n_all"], "n_comp_seeds": p["comp_nums"]["n_comp_seeds"],
        "usable_seed_frac": round(p["redundancy"]["usable_frac"], 3),
        "classifiable_frac": round(p["classifiable_frac"], 3),
        "necessity": bool(p["necessity"]), "necessity_mean": bool(p["necessity_by_mode"]["mean"]),
        "necessity_zero": bool(p["necessity_by_mode"]["zero"]),
        "prev_ablate_acc_mean": round(p["modes"]["mean"]["prev_ablate"][0], 4),
        "ind_ablate_acc_mean": round(p["modes"]["mean"]["ind_ablate"][0], 4),
        "prev_ablate_acc_zero": round(p["modes"]["zero"]["prev_ablate"][0], 4),
        "ind_ablate_acc_zero": round(p["modes"]["zero"]["ind_ablate"][0], 4),
        "prev_control_acc": round(p["modes"]["mean"]["prev_control"][0], 4),
        "ind_control_acc": round(p["modes"]["mean"]["ind_control"][0], 4),
        "specificity": bool(p["specificity"]),
        "prev_redundant": bool(p["redundancy"]["prev_redundant"]),
        "ind_redundant": bool(p["redundancy"]["ind_redundant"]),
        "composition": bool(p["composition"]),
        "comp_drop_prev": round(p["comp_nums"]["drop_prev"], 4),
        "comp_drop_nonprev_control": round(p["comp_nums"]["drop_ctrl"], 4),
        "tau_grid_agree_frac": round(result["tau_grid_agree_frac"], 3),
    }
    if "prev_max_single_drop" in p["redundancy"]:
        flags["prev_max_single_drop"] = round(p["redundancy"]["prev_max_single_drop"][0], 4)
        flags["ind_max_single_drop"] = round(p["redundancy"]["ind_max_single_drop"][0], 4)
        flags["prev_class_drop"] = round(p["redundancy"]["prev_class_drop"][0], 4)
        flags["ind_class_drop"] = round(p["redundancy"]["ind_class_drop"][0], 4)

    # ---- validity gates (review if fail) ----
    if p["n_trained"] < max(2, 0.5 * p["n_all"]) or p["base_acc"][0] < result["S"]:
        return _v("review", "base_not_inducting", flags)            # too few seeds learned induction
    if p["classifiable_frac"] < cfg.usable_frac:
        return _v("review", "circuit_not_classifiable", flags)      # prev+induction heads absent in most trained seeds
    if p["necessity_by_mode"]["mean"] != p["necessity_by_mode"]["zero"]:
        return _v("review", "mean_zero_disagree", flags)            # zero-ablation OOD artifact
    if result["tau_grid_agree_frac"] < cfg.usable_frac:
        return _v("review", "tau_fragile", flags)

    # ---- verdict ladder (redundancy is a CHARACTERIZATION, not a validity gate: head COUNT varies
    #      across seeds, so it is only assessed where >=half the trained seeds have >=2 heads/class) ----
    if not (p["necessity"] and p["specificity"]):
        return _v("pass", "circuit_not_clean", flags)
    if not p["composition"]:
        return _v("pass", "circuit_necessary_specific_not_composed", flags)
    if p["redundancy"]["usable_frac"] < 0.5:
        return _v("pass", "circuit_necessary_specific_composed_redundancy_unassessed", flags)
    if p["redundancy"]["prev_redundant"] and p["redundancy"]["ind_redundant"]:
        return _v("pass", "circuit_necessary_specific_composed_and_redundant", flags)
    return _v("pass", "circuit_necessary_specific_composed_concentrated", flags)


def _v(status, verdict, flags):
    return {"status": status, "decision": verdict, "verdict": verdict, "flags": flags}

__all__ = ["PRIMARY_VERDICTS", "REVIEW_VERDICTS", "decide_induction_circuit"]
