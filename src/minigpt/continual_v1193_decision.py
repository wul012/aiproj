"""Pure verdict logic for the v1193 continual-learning experiment."""

from __future__ import annotations

from typing import Any

from minigpt.experiment_utils import significant

REVIEW_VERDICTS = {"task_a_not_consolidated", "task_b_not_learned", "not_jointly_learnable",
                   "operand_leak", "no_forgetting_floor"}
PRIMARY_VERDICTS = {
    "no_catastrophic_forgetting",
    "catastrophic_forgetting_mitigated_by_replay",
    "catastrophic_forgetting_not_mitigated_by_replay",
    "partial_forgetting_mitigated_by_replay",
    "partial_forgetting_not_mitigated_by_replay",
}


def decide_continual(result: dict, cfg: Any) -> dict:
    """Pure gates + multi-signal verdict ladder with real null branches. No single cutoff
    decides the headline: forgetting needs a significant drop vs the consolidated plateau
    AND a clean continue-on-A floor; 'catastrophic' needs a drop to near chance; replay
    mitigation needs BOTH a significant reduction AND wrong-replay failing to help."""
    s = result
    chance = s["chance"]
    plat_m, plat_s = s["accA_plateau"]
    nf_m, nf_s = s["naive_forget"]
    after_m, after_s = s["naive_accA_after_B"]
    prior = s["b_majority_prior"]

    def reduces(less, more):
        """True iff `less` forgetting is meaningfully below `more` (margin AND combined std)."""
        (lm, ls), (mm, ms) = less, more
        return (mm - lm) > cfg.min_reduction and significant(mm, ms, lm, ls)

    g_consol = plat_m >= cfg.plateau_acc - 0.02
    g_b_learned = (s["naive_accB_after_B"][0] - prior) >= cfg.b_learn_margin
    # jointly learnable = the shared weights CAN hold BOTH tasks well above the majority-class
    # prior (so sequential loss is INTERFERENCE, not incapacity). NOT gated on hitting A's solo
    # plateau -- multiply-mod-p has a genuinely lower ceiling than addition at this scale.
    g_joint = ((s["joint_accA"][0] - prior) >= cfg.b_learn_margin) and \
              ((s["joint_accB"][0] - prior) >= cfg.b_learn_margin)
    g_leak = bool(s["leak_free"])
    g_floor = s["continue_on_A_forget"][0] <= cfg.floor_tol

    # findings (all reductions use the margin-aware `reduces`)
    forgets = (nf_m > cfg.min_reduction) and significant(plat_m, plat_s, after_m, after_s)
    catastrophic = after_m < cfg.catastrophic_chance_mult * chance
    rf = s["replay_forget"]
    replay_reduces = reduces(rf[s["replay_max_bs"]], s["naive_forget"])
    wrong_reduces = reduces(s["wrong_replay_forget"], s["naive_forget"])
    replay_specific = replay_reduces and (not wrong_reduces)
    bs_sorted = sorted(rf)
    monotone = all(rf[bs_sorted[i]][0] >= rf[bs_sorted[i + 1]][0] - 1e-9 for i in range(len(bs_sorted) - 1))
    # structure vs drift: does real-B forget MEANINGFULLY more than random-label-B?
    structure_specific = reduces(s["random_label_B_forget"], s["naive_forget"])

    flags = {
        "g_a_consolidated": g_consol, "g_b_learned": g_b_learned, "g_jointly_learnable": g_joint,
        "g_no_operand_leak": g_leak, "g_floor_clean": g_floor,
        "forgets": bool(forgets), "catastrophic": bool(catastrophic),
        "replay_reduces_forgetting": bool(replay_reduces), "wrong_replay_reduces": bool(wrong_reduces),
        "replay_specific": bool(replay_specific), "replay_dose_response_monotone": bool(monotone),
        "forgetting_is_task_structure_specific": bool(structure_specific),
        "forgetting_is_distribution_shift_not_structure": bool(not structure_specific),
        "savings_fast_masking": bool(s["recovered_k"] is not None and s["recovered_k"] <= 50),
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

    if not forgets:
        return _v("pass", "no_catastrophic_forgetting", flags)
    cat = "catastrophic" if catastrophic else "partial"
    if replay_specific:
        return _v("pass", f"{cat}_forgetting_mitigated_by_replay", flags)
    return _v("pass", f"{cat}_forgetting_not_mitigated_by_replay", flags)


def _v(status: str, verdict: str, flags: dict) -> dict:
    return {"status": status, "decision": verdict, "verdict": verdict, "flags": flags}

__all__ = ["PRIMARY_VERDICTS", "REVIEW_VERDICTS", "decide_continual"]
