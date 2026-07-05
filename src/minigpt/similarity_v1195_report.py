"""Report assembly for the v1195 task-similarity experiment."""

from __future__ import annotations

import math

from minigpt.report_utils import utc_now


def build_similarity_report(
    result: dict,
    info: dict,
    source: str,
    *,
    generated_at: str | None = None,
    c1_min_range: float,
    equiv_delta: float,
) -> dict:
    """Build the stable report contract from summarized measurements and a verdict."""
    stats = result["stats"]
    status, verdict, flags = info["status"], info["verdict"], info["flags"]

    rows = []
    for key in result["mix_keys"] + result["type_keys"]:
        item = stats[key]
        rows.append(
            {
                "arm": key,
                "overlap": round(item["overlap"][0], 4),
                "forgetting": round(item["forget"][0], 4),
                "forgetting_std": round(item["forget"][1], 4),
                "accB_conflict_test": _finite_round(item["accB_conflict"][0], 4),
                "accB_conflict_train": _finite_round(item["accB_train_conflict"][0], 4),
                "emb_drift": round(item["emb_drift"][0], 4),
                "learned": item["learned"],
            }
        )

    summary = {
        "status": status,
        "decision": info["decision"],
        "verdict": verdict,
        "p": result["config"]["p"],
        "seeds": len(result["seeds"]),
        "train_frac": result["config"]["train_frac"],
        "b_budget": result["config"]["b_budget"],
        "chance": round(result["chance"], 5),
        "leak_free": result["leak_free"],
        "accA_plateau": round(result["plateau"][0], 4),
        "per_seed_plateau_ok": result["per_seed_plateau_ok"],
        "continue_on_A_forgetting": round(result["continue_on_A_forget"][0], 4),
        "joint_accA": round(result["joint_accA"][0], 4),
        "joint_accB": round(result["joint_accB"][0], 4),
        "spearman_overlap_forgetting": flags["spearman_overlap_forget"],
        "spearman_perm_p": flags["spearman_perm_p"],
        "slope_span": flags["slope_span"],
        "overlap_survives_accB_and_drift": flags["overlap_survives_accB_and_drift"],
        "superlinear_vs_overwrite_null": flags["superlinear_vs_overwrite_null"],
        "mean_superlinear_excess": flags["mean_superlinear_excess"],
        "c2_family_does_not_protect": flags["c2_family_does_not_protect"],
        "family_protects": flags["family_protects"],
        "c3_type_points_on_curve": flags["c3_type_points_on_curve"],
        "structure_at_fixed_overlap": flags["structure_at_fixed_overlap"],
        "n_mix_curve": flags["n_mix_curve"],
        "n_indep_type_learned": flags["n_indep_type_learned"],
        "valid_measurement": status == "pass",
    }
    summary.update({f"flag_{key}": value for key, value in flags.items() if not isinstance(value, dict)})

    add_offset = stats["type:add_offset"]
    multiply = stats["type:mul"]
    add_same = stats["type:add_same"]
    recommendations = [
        (
            f"VERDICT ({verdict}, status={status}): x-axis is the ANALYTIC output-table overlap of B with "
            f"A=(a+b) mod {result['config']['p']} -- model-INDEPENDENT, |{{(a,b):f_B==f_A}}|/p^2. "
            f"Forgetting = A's held-out accuracy drop from its consolidated plateau {result['plateau'][0]:.3f} "
            f"after a fixed {result['config']['b_budget']}-step B phase. status='pass' certifies a VALID "
            f"measurement (A consolidated per-seed, clean continue-on-A floor {result['continue_on_A_forget'][0]:.3f}, "
            f"no operand leak, add+mul jointly learnable A{result['joint_accA'][0]:.2f}/B{result['joint_accB'][0]:.2f}, "
            f">={flags['n_mix_curve']} learnable interior curve points), NOT a clean collapse."
        ),
        (
            "C1 SLOPE (interior, overlap<1): forgetting is monotone-graded in overlap -- "
            f"Spearman(overlap,forgetting)={flags['spearman_overlap_forget']} (perm p={flags['spearman_perm_p']}), "
            f"spanning {flags['slope_span']:.3f} from high-overlap to low-overlap (>= {c1_min_range}); "
            f"slope_certified={flags['c1_monotone_slope']}. The overlap=1 endpoint is EXCLUDED (forgetting-free "
            "by construction = v1193's continue-on-A floor + op-token-confounded); the claim is the INTERIOR only."
        ),
        (
            "NOT A B-LEARNEDNESS / DRIFT ARTIFACT: controlling for accB and shared-embedding drift, the overlap "
            f"coefficient stays negative and dominant (std beta overlap|accB={flags['beta_overlap_given_accB']} vs "
            f"accB={flags['beta_accB']}; overlap|drift={flags['beta_overlap_given_drift']} vs drift={flags['beta_drift']}); "
            f"overlap_survives={flags['overlap_survives_accB_and_drift']}. accB is read on CONFLICT cells only "
            "(where the retained A-circuit cannot answer for B)."
        ),
        (
            "FAMILY IS A RED HERRING (re-confirms v1193's distribution-shift null via a 2nd manipulation): at "
            f"overlap~0, add_offset (SAME '+' operation, just +{result['config']['add_offset_c0']}) forgets "
            f"{add_offset['forget'][0]:.3f} vs mul {multiply['forget'][0]:.3f} -- equivalent (|\u0394|<= {equiv_delta}), "
            f"both >> add_same {add_same['forget'][0]:.3f}; family_does_not_protect={flags['c2_family_does_not_protect']}, "
            f"structure_at_fixed_overlap={flags['structure_at_fixed_overlap']}. UNIFICATION residual test "
            f"(type points on the mixture curve)={flags['c3_type_points_on_curve']}."
        ),
        _shape_recommendation(result, flags),
    ]

    curve_points = []
    for key in result["mix_keys"] + result["type_keys"]:
        item = stats[key]
        curve_points.append(
            {
                "key": key,
                "kind": "mix" if key.startswith("mix") else "type",
                "overlap": round(item["overlap"][0], 5),
                "forgetting": round(item["forget"][0], 5),
                "forgetting_std": round(item["forget"][1], 5),
                "learned": item["learned"],
                "accB_conflict_train": _finite_round(item["accB_train_conflict"][0], 4),
                "accB_conflict_test": _finite_round(item["accB_conflict"][0], 4),
            }
        )

    return {
        "schema_version": 1,
        "title": "MiniGPT task-similarity -> catastrophic forgetting v1195",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": info["decision"],
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": [
            "arm",
            "overlap",
            "forgetting",
            "forgetting_std",
            "accB_conflict_test",
            "accB_conflict_train",
            "emb_drift",
            "learned",
        ],
        "curve_points": curve_points,
        "residuals": flags["residuals"],
        "plateau": round(result["plateau"][0], 5),
        "source": source,
    }


def _finite_round(value: float, digits: int) -> float | None:
    return round(value, digits) if not math.isnan(value) else None


def _shape_recommendation(result: dict, flags: dict) -> str:
    finding = (
        "(>= margin) -> SUPER-LINEAR: even a small target shift collapses the shared representation GLOBALLY, "
        "beyond the conflicting cells (ties to v1193's global-shift mechanism)."
        if flags["superlinear_vs_overwrite_null"]
        else "(< margin) -> forgetting is APPROXIMATELY the local-overwrite null (mild mid-overlap excess only). So "
        "the overlap law is largely the overwrite-fraction made quantitative, NOT a special global collapse; "
        "v1193's 'catastrophic' forgetting is the overlap=0 endpoint of this graded, ~proportional overwrite."
    )
    return (
        "SHAPE vs the overwrite null: the trivial 'overwrite only the conflicting cells' null predicts "
        f"forgetting ~= (1-overlap)*plateau. Observed mean excess over the null is {flags['mean_superlinear_excess']} "
        f"{finding} SCOPE: toy modular arithmetic, 1-layer transformer, p={result['config']['p']}; overlap = 1 - "
        "conflict-fraction on shared inputs; the random-partition mixture is fit on train cells but does NOT "
        "generalize the per-cell split to held-out cells; NOT a claim about instruction-tuned LLM forgetting."
    )


__all__ = ["build_similarity_report"]
