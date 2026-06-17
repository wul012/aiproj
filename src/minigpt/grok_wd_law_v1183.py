"""v1183: weight-decay dose-response for grokking — from a binary claim to a law.

v1179 established the binary causal claim "weight decay drives grokking": at
weight_decay=1.0 all seeds grok, at weight_decay=0.0 none do. v1180-v1182 then
audited that single artifact (evidence reconstruction, curve phases, paired
contrast) without running new training. v1183 advances the *science*: it sweeps
the weight-decay STRENGTH over `a + b = c (mod 97)` and measures how the
generalization step `t_gen` depends on it, turning the binary claim into a
dose-response.

It deliberately reuses the v1179 training primitive (`grok_v1179.train_arm`) and
its censoring-aware aggregator, so the per-arm dynamics are byte-identical to
v1179 — only the weight-decay grid and the cross-arm trend analysis are new.

Hypothesis: stronger weight decay grokks SOONER (t_gen decreases as wd grows),
and below some threshold wd the model memorizes but never groks within budget.
The honest counter-possibilities the verdict must allow: the trend may be
non-monotone, only a threshold may be visible without a step-trend, or very large
wd may break memorization entirely (the upper limit of the dose-response).

Honest-measurement contract (project house rules):
* `status == "pass"` IFF VALIDLY MEASURED — task correct, the reference arm
  (wd nearest 1.0) memorizes every seed (training works), and the seed x wd grid
  is complete. NOT gated on whether a clean law appears.
* Multi-seed, paired within a seed (identical init + split across all wd arms,
  vary only weight_decay), so the dose-response is not confounded by init/split.
* The grok step is high-variance and censored (a seed may not grok within budget),
  so per-wd we report grok_rate and average t_gen only over the seeds that grokked.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch

from minigpt.grok_v1179 import (
    GrokConfig,
    arm_aggregate,
    beats_lower,
    build_modular_task,
    make_grok_model,
    split_indices,
    train_arm,
    verify_task,
)
from minigpt.report_utils import utc_now
from minigpt.script_runtime import seed_everything

# The default weight-decay grid: 0.0 (the v1179 anchor that never groks) up to a
# strong value, roughly log-spaced to expose a monotone trend if one exists.
DEFAULT_WDS = (0.0, 0.1, 0.3, 1.0, 3.0)


@dataclass
class WdLawConfig:
    """Hyperparameters for the weight-decay sweep. Mirrors the grokking-regime
    settings of v1179 (train_frac=0.2, 1-layer/128, full-batch AdamW) plus the
    sweep grid. The per-arm training itself is delegated to ``grok_v1179.train_arm``
    via a derived ``GrokConfig``."""

    p: int = 97
    train_frac: float = 0.2
    n_layer: int = 1
    n_head: int = 4
    n_embd: int = 128
    lr: float = 1e-3
    max_steps: int = 40000
    eval_every: int = 200
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341)
    wds: tuple[float, ...] = DEFAULT_WDS

    def grok_config(self) -> GrokConfig:
        """A ``GrokConfig`` carrying the per-arm training hyperparameters (the
        ``wds`` field is unused here — v1183 drives the sweep itself)."""
        return GrokConfig(
            p=self.p, train_frac=self.train_frac, n_layer=self.n_layer, n_head=self.n_head,
            n_embd=self.n_embd, lr=self.lr, max_steps=self.max_steps, eval_every=self.eval_every,
            seeds=self.seeds,
        )


def decide_wd_law(config: WdLawConfig, results_by_wd: dict[float, list[dict]], g0_task_correct: bool) -> dict:
    """Apply validity gates and classify the dose-response.

    Verdict ladder:
      no_memorization_training_broken        -- the reference arm can't even memorize.
      insufficient_grok_range_to_characterize-- fewer than 2 wd values grok in budget.
      wd_dose_response_monotone_acceleration -- t_gen strictly decreases across the
                                                grokking wds AND the strongest grokking
                                                wd groks significantly sooner than the weakest.
      wd_accelerates_grok_nonmonotone        -- strongest groks significantly sooner, but
                                                the trend is not strictly monotone.
      wd_threshold_without_clear_step_trend  -- a grok threshold exists but no separable
                                                step-trend among the grokking wds.
    """
    wds_sorted = sorted(config.wds)
    aggs = {wd: arm_aggregate(results_by_wd.get(wd, [])) for wd in wds_sorted}
    n_seeds = len(config.seeds)

    ref_wd = min(wds_sorted, key=lambda w: abs(w - 1.0))
    g1_memorization = aggs[ref_wd]["n"] > 0 and aggs[ref_wd]["mem_rate"] >= 0.999
    g2_grid_complete = all(aggs[wd]["n"] == n_seeds for wd in wds_sorted)
    status = "pass" if (g0_task_correct and g1_memorization and g2_grid_complete) else "review"

    grok_wds = [wd for wd in wds_sorted if aggs[wd]["grok_rate"] >= 0.6]
    threshold_wd = grok_wds[0] if grok_wds else None
    censored_below_threshold = bool(grok_wds) and grok_wds[0] > wds_sorted[0]
    strongest_wd = wds_sorted[-1]
    too_much_wd_breaks_memorization = aggs[strongest_wd]["mem_rate"] < 0.999
    # The strongest decay memorizes but fails to grok within budget -> the upper
    # arm of an interior optimum, distinct from breaking memorization outright.
    high_end_grok_censored = aggs[strongest_wd]["grok_rate"] < 0.6 and aggs[strongest_wd]["mem_rate"] >= 0.999
    interior_optimum = bool(grok_wds) and aggs[strongest_wd]["grok_rate"] < 0.6
    best_wd = min(grok_wds, key=lambda w: aggs[w]["t_gen_mean"]) if grok_wds else None

    monotone = False
    accelerates_significant = False
    if len(grok_wds) >= 2:
        t_gens = [aggs[wd]["t_gen_mean"] for wd in grok_wds]
        monotone = all(t_gens[i] > t_gens[i + 1] for i in range(len(t_gens) - 1))
        lo, hi = grok_wds[0], grok_wds[-1]
        accelerates_significant = beats_lower(
            aggs[hi]["t_gen_mean"], aggs[hi]["t_gen_std"], aggs[lo]["t_gen_mean"], aggs[lo]["t_gen_std"]
        )

    if not g1_memorization:
        verdict = "no_memorization_training_broken"
    elif len(grok_wds) < 2:
        verdict = "insufficient_grok_range_to_characterize"
    elif interior_optimum:
        # The strongest decay does NOT grok in budget despite memorizing -> the
        # relationship is non-monotone with an interior optimum (fastest at a
        # middle wd; both too-little and too-much decay fail to grok in budget).
        verdict = "wd_dose_response_interior_optimum"
    elif monotone and accelerates_significant:
        verdict = "wd_dose_response_monotone_acceleration"
    elif accelerates_significant:
        verdict = "wd_accelerates_grok_nonmonotone"
    else:
        verdict = "wd_threshold_without_clear_step_trend"

    return {
        "status": status,
        "verdict": verdict,
        "gates": {
            "g0_task_correct": g0_task_correct,
            "g1_memorization": g1_memorization,
            "g2_grid_complete": g2_grid_complete,
        },
        "aggs": aggs,
        "grok_wds": grok_wds,
        "threshold_wd": threshold_wd,
        "best_wd": best_wd,
        "censored_below_threshold": censored_below_threshold,
        "high_end_grok_censored": high_end_grok_censored,
        "interior_optimum": interior_optimum,
        "too_much_wd_breaks_memorization": too_much_wd_breaks_memorization,
        "monotone": monotone,
        "accelerates_significant": accelerates_significant,
    }


def run_wd_law(*, config: WdLawConfig, device: torch.device, generated_at: str | None = None) -> dict:
    """Run the weight-decay sweep and return a readability report dict."""
    p = config.p
    vocab_size = p + 2
    full_data = build_modular_task(p)
    g0_task_correct = verify_task(full_data, p)
    gcfg = config.grok_config()

    results_by_wd: dict[float, list[dict]] = {wd: [] for wd in config.wds}
    seed_rows: list[dict] = []
    curves: dict[str, list] = {str(wd): [] for wd in config.wds}

    for seed in config.seeds:
        seed_everything(seed)
        train_idx, val_idx = split_indices(full_data.shape[0], config.train_frac, seed)
        init_state = {k: v.detach().clone() for k, v in make_grok_model(vocab_size, gcfg).state_dict().items()}
        for wd in config.wds:
            result = train_arm(
                config=gcfg, vocab_size=vocab_size, full_data=full_data,
                train_idx=train_idx, val_idx=val_idx, init_state=init_state,
                weight_decay=wd, device=device,
            )
            results_by_wd[wd].append(result)
            curves[str(wd)].append(result["curve"])
            seed_rows.append(
                {
                    "seed": seed, "weight_decay": wd,
                    "memorized": result["memorized"], "grokked": result["grokked"],
                    "t_mem": result["t_mem"], "t_gen": result["t_gen"],
                    "grok_gap": result["grok_gap"], "val_at_mem": result["val_at_mem"],
                    "final_train_acc": result["final_train_acc"],
                    "final_val_acc": result["final_val_acc"], "steps_run": result["steps_run"],
                }
            )

    return assemble_report(config, results_by_wd, curves, seed_rows, g0_task_correct, generated_at)


def assemble_report(
    config: WdLawConfig,
    results_by_wd: dict[float, list[dict]],
    curves: dict[str, list],
    seed_rows: list[dict],
    g0_task_correct: bool,
    generated_at: str | None = None,
) -> dict:
    """Build the readability report from per-arm training results (no training).

    Split out from :func:`run_wd_law` so the verdict and report can be re-derived
    from cached results — training is deterministic, so a fresh ``run_wd_law`` and
    a re-assembly over the same results produce the identical report."""
    p = config.p
    info = decide_wd_law(config, results_by_wd, g0_task_correct)
    aggs = info["aggs"]

    # The dose-response table: one row per weight_decay (the headline rows).
    rows = []
    for wd in sorted(config.wds):
        agg = aggs[wd]
        rows.append(
            {
                "weight_decay": wd,
                "grok_rate": agg["grok_rate"],
                "mem_rate": agg["mem_rate"],
                "n_grokked": agg["n_grokked"],
                "t_gen_mean": agg["t_gen_mean"],
                "t_gen_std": agg["t_gen_std"],
                "grok_gap_mean": agg["grok_gap_mean"],
                "final_val_mean": agg["final_val_mean"],
            }
        )

    summary = {
        "p": p,
        "train_frac": config.train_frac,
        "n_layer": config.n_layer,
        "n_embd": config.n_embd,
        "max_steps": config.max_steps,
        "seeds": len(config.seeds),
        "wds": list(sorted(config.wds)),
        "verdict": info["verdict"],
        "g0_task_correct": info["gates"]["g0_task_correct"],
        "g1_memorization": info["gates"]["g1_memorization"],
        "g2_grid_complete": info["gates"]["g2_grid_complete"],
        "grok_wds": info["grok_wds"],
        "grok_threshold_wd": info["threshold_wd"],
        "fastest_grok_wd": info["best_wd"],
        "censored_below_threshold": info["censored_below_threshold"],
        "high_end_grok_censored": info["high_end_grok_censored"],
        "interior_optimum": info["interior_optimum"],
        "too_much_wd_breaks_memorization": info["too_much_wd_breaks_memorization"],
        "monotone_t_gen_decrease": info["monotone"],
        "strongest_groks_sooner_significant": info["accelerates_significant"],
        "boundary": "toy_scale_single_task_modular_addition_grokking_dose_response_not_a_scaling_claim",
    }

    return {
        "schema_version": 1,
        "title": "MiniGPT v1183 grokking weight-decay dose-response",
        "generated_at": generated_at or utc_now(),
        "status": info["status"],
        "decision": info["verdict"],
        "summary": summary,
        "rows": rows,
        "seed_rows": seed_rows,
        "curves": curves,
        "recommendations": _recommendations(info),
        "csv_fieldnames": [
            "weight_decay", "grok_rate", "mem_rate", "n_grokked",
            "t_gen_mean", "t_gen_std", "grok_gap_mean", "final_val_mean",
        ],
    }


def _recommendations(info: dict) -> list[str]:
    verdict = info["verdict"]
    if verdict == "wd_dose_response_interior_optimum":
        out = [
            f"Grokking weight-decay is non-monotone with an interior optimum: it groks fastest at weight_decay={info['best_wd']}, and both too little and too much decay fail to grok within budget.",
            f"Below weight_decay={info['threshold_wd']} the model memorizes but does not grok in budget; the strongest decay tested also memorizes but does not grok in budget (it does NOT break memorization).",
        ]
        return out
    if verdict == "wd_dose_response_monotone_acceleration":
        out = ["Weight decay grokking is a dose-response: the generalization step decreases monotonically as weight decay grows, and the strongest decay groks significantly sooner than the weakest."]
        if info["censored_below_threshold"]:
            out.append(f"A threshold is visible: below weight_decay={info['threshold_wd']} the model memorizes but does not grok within budget.")
        if info["too_much_wd_breaks_memorization"]:
            out.append("The largest weight decay breaks memorization — the upper limit of the dose-response.")
        return out
    if verdict == "wd_accelerates_grok_nonmonotone":
        return ["Stronger weight decay groks significantly sooner overall, but the per-step trend across the grid is not strictly monotone."]
    if verdict == "wd_threshold_without_clear_step_trend":
        return ["A grok threshold in weight decay exists, but the grokking weight-decays do not show a separable step-trend at this budget/seed count."]
    if verdict == "insufficient_grok_range_to_characterize":
        return ["Fewer than two weight-decay values grok within budget — cannot characterize a dose-response (widen the grid or increase max_steps)."]
    return ["The reference weight-decay arm failed to memorize the train set — training is broken; not a valid dose-response measurement."]


__all__ = ["WdLawConfig", "DEFAULT_WDS", "decide_wd_law", "assemble_report", "run_wd_law"]
