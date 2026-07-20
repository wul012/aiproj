"""Report assembly for the v1192 calibration experiment."""

from __future__ import annotations

from minigpt.experiment_utils import mean_std
from minigpt.report_utils import utc_now


def _arm_row(name: str, a: dict) -> dict:
    dm, ds = mean_std(a["dECE"])
    return {
        "arm": name, "T": round(a["T"][0], 4), "T_std": round(a["T"][1], 4),
        "ece": round(a["ece"][0], 5), "ece_T": round(a["ece_T"][0], 5),
        "delta_ece_mean": round(dm, 5), "delta_ece_std": round(ds, 5),
        "nll": round(a["nll"][0], 5), "nll_T": round(a["nll_T"][0], 5),
        "kl": round(a["kl"][0], 5), "kl_T": round(a["kl_T"][0], 5),
        "brier": round(a["brier"][0], 5), "conf": round(a["conf"][0], 4), "acc": round(a["acc"][0], 4),
    }


def build_calibration_report(
    result: dict,
    info: dict,
    source: str,
    *,
    generated_at: str | None = None,
    seed_count: int,
) -> dict:
    """Assemble the 5-format readability report from the analysis ``result`` + ``decide`` info."""

    h = result["arms"]["hard_ce"]
    ctl = result["controls"]
    cm = result["comovement"]
    status, verdict, flags = info["status"], info["verdict"], info["flags"]

    rows = [_arm_row(n, result["arms"][n]) for n in ("hard_ce", "soft_distill", "label_smooth", "random_init")
            if n in result["arms"]]
    rows.append(_arm_row("boundary_low_entropy", result["boundary"]))

    summary = {
        "status": status, "decision": info["decision"], "verdict": verdict,
        "headline_n": result["headline_n"], "seeds": seed_count,
        "mean_true_entropy_nats": result["mean_H"], "entropy_spread": result["entropy_spread"],
        "uniform_kl_floor": result["uniform_kl_floor"],
        "oracle_analytic_ece": result["oracle_ece"],
        "oracle_sampled_ece_floor": result["oracle_sampled_ece"],
        "hard_ce_kl": round(h["kl"][0], 5), "hard_ce_mean_conf": round(h["conf"][0], 4),
        "hard_ce_mean_acc": round(h["acc"][0], 4),
        "hard_ce_overconfidence_gap": round(h["conf"][0] - h["acc"][0], 4),
        "hard_ce_ece": round(h["ece"][0], 5), "hard_ce_ece_std": round(h["ece"][1], 5),
        "fitted_T": round(h["T"][0], 4), "fitted_T_std": round(h["T"][1], 4),
        "hard_ce_ece_after_T": round(h["ece_T"][0], 5),
        "paired_delta_ece": round(mean_std(h["dECE"])[0], 5), "paired_delta_ece_std": round(mean_std(h["dECE"])[1], 5),
        "kl_after_T": round(h["kl_T"][0], 5),
        "rel_ece_reduction": cm["rel_dECE"], "rel_kl_reduction": cm["rel_dKL"], "calibration_kl_co_move": cm["co_move"],
        "wrong_T_value": ctl["wrong_T_value"], "ece_fitted_T": ctl["ece_fitted_T"], "ece_wrong_T": ctl["ece_wrong_T"],
        "calibrated_ece_pre": ctl["calibrated_ece_pre"], "calibrated_ece_post_headlineT": ctl["calibrated_ece_post_headlineT"],
        "boundary_mean_H": result["boundary_mean_H"], "boundary_gap": result["boundary_gap"],
        "boundary_overconfident": result["boundary_overconfident"], "boundary_correctable": result["boundary_correctable"],
        "binning_robust": result["binning_robust"], "not_magic_T_to_one": result["not_magic_T_to_one"],
        "teacher_kl_to_true": result["teacher_kl"],
        "valid_measurement": status == "pass",
    }
    summary.update({f"flag_{k}": v for k, v in flags.items()})

    recs = [
        (f"VERDICT ({verdict}): on a SYNTHETIC Dirichlet next-char task (K contexts, M=5, KNOWN P_true; "
         f"mean entropy {result['mean_H']:.3f} nats, spread {result['entropy_spread']:.2f}), a 2L/32 transformer "
         f"trained with hard CE at n={result['headline_n']} samples/ctx is OVERCONFIDENT: mean confidence "
         f"{h['conf'][0]:.3f} >> mean accuracy {h['acc'][0]:.3f} (gap +{h['conf'][0]-h['acc'][0]:.3f}), analytic "
         f"ECE {h['ece'][0]:.3f}±{h['ece'][1]:.3f} >> the EXACT oracle floor {result['oracle_ece']:.3f}. "
         f"status='{status}' certifies a VALID measurement (model beats uniform KL {result['uniform_kl_floor']:.3f}, "
         f"real entropy spread, identified T, non-degenerate bins), NOT a flattering magnitude."),
        (f"FIX: one GLOBAL temperature T={h['T'][0]:.2f}±{h['T'][1]:.2f} (>1, fit by NLL over all contexts) reduces "
         f"ECE {h['ece'][0]:.3f}->{h['ece_T'][0]:.3f} (paired Δ {mean_std(h['dECE'])[0]:.3f}±{mean_std(h['dECE'])[1]:.3f}, "
         f"lb>0={flags['correction_paired_significant']}) toward the floor. PAIRED per-seed test (shared model+contexts), "
         f"not the unpaired in-quadrature test."),
        (f"SPECIFIC (not 'any flattening helps'): ECE-vs-T is U-shaped with its minimum at the fitted T (u_shaped="
         f"{ctl['u_shaped']}); a mismatched T={ctl['wrong_T_value']} from a more-overconfident regime gives higher ECE "
         f"({ctl['ece_wrong_T']:.3f} vs fitted {ctl['ece_fitted_T']:.3f}, wrong_T_worse={ctl['wrong_T_worse']}); the same T "
         f"does NOT help an already-calibrated model ({ctl['calibrated_ece_pre']:.3f}->{ctl['calibrated_ece_post_headlineT']:.3f}, "
         f"t_not_helping_calibrated={ctl['t_not_helping_calibrated']}); and the oracle's own analytic ECE is {result['oracle_ece']:.3f}≈0."),
        (f"NOT MAGIC — finite-sample MLE artifact: across the samples/ctx sweep the fitted T trends toward 1 as n grows "
         f"(not_magic_T_to_one={result['not_magic_T_to_one']}; "
         + ", ".join(f"n={n}:T={result['sweep'][n]['T'][0]:.2f}" for n in sorted(result['sweep'])) + "). "
         "Overconfidence is the few-sample collapse toward the sampled mode, not an intrinsic architectural property."),
        (f"NOVELTY vs v1173 (honest): expected-NLL = entropy + KL, so on this substrate ECE and KL CO-MOVE under "
         f"temperature (rel ECE reduction {cm['rel_dECE']:.2f} ≈ rel KL reduction {cm['rel_dKL']:.2f}, co_move={cm['co_move']}) "
         f"— we do NOT claim an ECE/KL dissociation. Calibration adds beyond KL: (a) DIRECTION (KL is direction-blind; ECE "
         f"diagnoses OVER- vs under-confidence) and (b) the actionable single-scalar fix, measured against an EXACT oracle floor. "
         f"soft_distill is already calibrated (T={result['arms']['soft_distill']['T'][0]:.2f}, calibrated={flags['soft_distill_calibrated']}) "
         f"— a consistency check with v1173, not new novelty."),
        (f"BOUNDARY (the null): a LOW-entropy task instance (mean H {result['boundary_mean_H']:.3f}) is only marginally "
         f"overconfident (gap +{result['boundary_gap']:.3f} vs +{h['conf'][0]-h['acc'][0]:.3f} at high H) and crucially NOT "
         f"correctable by temperature (ECE {result['boundary']['ece'][0]:.3f}->{result['boundary']['ece_T'][0]:.3f}, "
         f"correctable={result['boundary_correctable']}) — the correctable-overconfidence phenomenon needs real aleatoric "
         "uncertainty; at low H there is little GLOBAL over-confidence and one scalar cannot touch the per-context residual. "
         f"SAMPLED ECE has a positive Jensen-bias floor (oracle sampled-ECE {result['oracle_sampled_ece']:.3f}>0) — exactly why "
         "the headline uses ANALYTIC metrics (oracle floor 0). SCOPE: synthetic aleatoric categorical, few-sample regime; "
         "NOT a claim that transformers are overconfident in general."),
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT calibration under uncertainty + temperature scaling v1192",
        "generated_at": generated_at or utc_now(),
        "status": status, "decision": info["decision"],
        "summary": summary, "rows": rows,
        "recommendations": recs,
        "csv_fieldnames": ["arm", "T", "T_std", "ece", "ece_T", "delta_ece_mean", "delta_ece_std",
                           "nll", "nll_T", "kl", "kl_T", "brier", "conf", "acc"],
        "sweep": {str(n): {"T": result["sweep"][n]["T"][0], "ece": result["sweep"][n]["ece"][0],
                           "conf": result["sweep"][n]["conf"][0], "acc": result["sweep"][n]["acc"][0],
                           "kl": result["sweep"][n]["kl"][0]} for n in sorted(result["sweep"])},
        "fig_ece_vs_T": result["fig_ece_vs_T"], "fig_T_fitted": result["fig_T_fitted"],
        "fig_reliability_pre": result["fig_reliability_pre"], "fig_reliability_post": result["fig_reliability_post"],
        "source": source,
    }


__all__ = ["build_calibration_report"]
