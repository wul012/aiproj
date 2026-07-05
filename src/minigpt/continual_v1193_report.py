"""Report assembly for the v1193 continual-learning experiment."""

from __future__ import annotations

from minigpt.report_utils import utc_now

def build_report(result: dict, info: dict, source: str, *, generated_at: str | None = None) -> dict:
    """Assemble the 5-format readability report from summarize() result + decide() info."""
    s = result
    status, verdict, flags = info["status"], info["verdict"], info["flags"]
    chance = s["chance"]

    rows = [
        {"arm": "consolidated_A", "acc_A": round(s["accA_plateau"][0], 4), "acc_A_std": round(s["accA_plateau"][1], 4),
         "forgetting": 0.0, "note": "plateau (A learned)"},
        {"arm": "naive_sequential", "acc_A": round(s["naive_accA_after_B"][0], 4), "acc_A_std": round(s["naive_accA_after_B"][1], 4),
         "forgetting": round(s["naive_forget"][0], 4), "note": f"after B; acc_B={s['naive_accB_after_B'][0]:.3f}"},
        {"arm": "continue_on_A", "acc_A": round(s["accA_plateau"][0] - s["continue_on_A_forget"][0], 4), "acc_A_std": 0.0,
         "forgetting": round(s["continue_on_A_forget"][0], 4), "note": "floor (no shift)"},
        {"arm": "random_label_B", "acc_A": round(s["accA_plateau"][0] - s["random_label_B_forget"][0], 4), "acc_A_std": 0.0,
         "forgetting": round(s["random_label_B_forget"][0], 4), "note": "null: structure vs drift"},
        {"arm": "wrong_replay_B", "acc_A": round(s["accA_plateau"][0] - s["wrong_replay_forget"][0], 4), "acc_A_std": 0.0,
         "forgetting": round(s["wrong_replay_forget"][0], 4), "note": "replay B not A (must still forget)"},
        {"arm": "multitask_joint", "acc_A": round(s["joint_accA"][0], 4), "acc_A_std": round(s["joint_accA"][1], 4),
         "forgetting": 0.0, "note": f"upper bound; acc_B={s['joint_accB'][0]:.3f}"},
    ]
    for bs in sorted(s["replay_forget"]):
        rows.append({"arm": f"replay_buffer_{bs}", "acc_A": round(s["accA_plateau"][0] - s["replay_forget"][bs][0], 4),
                     "acc_A_std": round(s["replay_forget"][bs][1], 4), "forgetting": round(s["replay_forget"][bs][0], 4),
                     "note": "A-train replay" if bs else "= naive floor"})

    summary = {
        "status": status, "decision": info["decision"], "verdict": verdict,
        "task_a": s["config"]["task_a"], "task_b": s["config"]["task_b"], "p": s["config"]["p"],
        "chance": round(chance, 5), "b_majority_prior": round(s["b_majority_prior"], 4), "leak_free": s["leak_free"],
        "seeds": len(s["seeds"]), "train_frac": s["config"]["train_frac"], "b_budget": s["config"]["b_budget"],
        "accA_plateau": round(s["accA_plateau"][0], 4),
        "naive_accA_after_B": round(s["naive_accA_after_B"][0], 4),
        "naive_forgetting": round(s["naive_forget"][0], 4), "naive_forgetting_std": round(s["naive_forget"][1], 4),
        "naive_accB_after_B": round(s["naive_accB_after_B"][0], 4),
        "continue_on_A_forgetting": round(s["continue_on_A_forget"][0], 4),
        "random_label_B_forgetting": round(s["random_label_B_forget"][0], 4),
        "wrong_replay_forgetting": round(s["wrong_replay_forget"][0], 4),
        "replay_max_buffer": s["replay_max_bs"],
        "replay_max_forgetting": round(s["replay_forget"][s["replay_max_bs"]][0], 4),
        "joint_accA": round(s["joint_accA"][0], 4), "joint_accB": round(s["joint_accB"][0], 4),
        "savings_recovered_k": s["recovered_k"],
        "valid_measurement": status == "pass",
    }
    summary.update({f"flag_{k}": v for k, v in flags.items()})

    recs = [
        (f"VERDICT ({verdict}): task A=({s['config']['task_a']}) consolidated to test acc {s['accA_plateau'][0]:.3f}; "
         f"after training task B=({s['config']['task_b']}) for {s['config']['b_budget']} steps A collapses to "
         f"{s['naive_accA_after_B'][0]:.3f} (chance {chance:.3f}) -> FORGETTING {s['naive_forget'][0]:.3f}±{s['naive_forget'][1]:.3f}. "
         f"status='{status}' certifies a VALID measurement (A consolidated to a plateau, B genuinely learned "
         f"{s['naive_accB_after_B'][0]:.3f} >> majority-prior {s['b_majority_prior']:.3f}, jointly learnable, no operand leak), "
         f"NOT a flattering result. 'catastrophic'={flags['catastrophic']} is gated on the drop reaching near chance."),
        (f"FLOOR & TRAJECTORY: continue-on-A (no distribution shift) forgets only {s['continue_on_A_forget'][0]:.3f} "
         f"(g_floor_clean={flags['g_floor_clean']}) — so forgetting needs a NEW distribution, not just more steps. "
         f"acc_A through the B phase: {s['traj_mean']} — collapse is {'sharp/instant' if len(s['traj_mean'])>1 and s['traj_mean'][1] < 0.3 else 'gradual'}."),
        (f"REPLAY (mitigation): replaying A-train examples during B reduces forgetting as a dose-response "
         + ", ".join(f"buf={bs}:{s['replay_forget'][bs][0]:.3f}" for bs in sorted(s['replay_forget']))
         + f" (monotone={flags['replay_dose_response_monotone']}); replay reduces forgetting={flags['replay_reduces_forgetting']}. "
         f"SPECIFIC (not 'any extra gradients'): WRONG-replay (replaying B, not A) still forgets {s['wrong_replay_forget'][0]:.3f} "
         f"(wrong_replay_reduces={flags['wrong_replay_reduces']}, replay_specific={flags['replay_specific']}). "
         "Replay works by RE-EXPOSING A data — it is data, not magic (the v1173 discipline)."),
        (f"HONEST MECHANISM: random-label-B (same B inputs, SHUFFLED targets) forgets {s['random_label_B_forget'][0]:.3f} "
         f"vs real-B {s['naive_forget'][0]:.3f} — task-structure-specific={flags['forgetting_is_task_structure_specific']}. "
         f"{'Real B forgets significantly more, so B-structure interferes.' if flags['forgetting_is_task_structure_specific'] else 'They forget about equally, so the forgetting is DISTRIBUTION-SHIFT-driven (training on a new input distribution overwrites the shared weights), NOT specific to B-task structure — reported honestly.'}"),
        (f"SAVINGS (erasure vs masking): relearning A reaches its plateau "
         + (f"in {s['recovered_k']} steps (fast => representational MASKING, A reused not erased)"
            if flags['savings_fast_masking'] else
            (f"in {s['recovered_k']} steps (slow => closer to ERASURE)" if s['recovered_k'] is not None
             else "only beyond the probed budget (slow => closer to ERASURE)"))
         + f". JOINT upper bound (no forgetting by construction): acc_A {s['joint_accA'][0]:.3f}, acc_B {s['joint_accB'][0]:.3f}. "
         "SCOPE: toy modular-arithmetic generalization on a 1-layer transformer; NOT a claim about instruction-tuned LLM forgetting."),
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT continual learning / catastrophic forgetting v1193",
        "generated_at": generated_at or utc_now(),
        "status": status, "decision": info["decision"],
        "summary": summary, "rows": rows, "recommendations": recs,
        "csv_fieldnames": ["arm", "acc_A", "acc_A_std", "forgetting", "note"],
        "traj_mean": s["traj_mean"],
        "replay_curve": {str(bs): round(s["replay_forget"][bs][0], 5) for bs in sorted(s["replay_forget"])},
        "source": source,
    }


__all__ = ["build_report"]
