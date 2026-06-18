"""v1191: causal frequency ablation — the interpretability capstone.

v1188 showed the grokked model's number-embeddings are Fourier-concentrated and
v1190 showed the output-logit addition-ridge sits on the same frequencies — but
both are *correlational* (named "supports", not "proves"). v1191 makes it causal:
it surgically removes Fourier frequencies from the (tied) number-embedding of the
shipped v1185 checkpoint and re-measures held-out accuracy.

Because ``lm_head.weight`` is tied to ``token_embedding.weight``, filtering the
number rows hits BOTH the input representation and the output readout at once.

Three interventions answer necessity / specificity / sufficiency:
  * remove the top-k dominant frequencies  -> if accuracy COLLAPSES, they are NECESSARY;
  * remove k RANDOM non-dominant frequencies -> if accuracy HOLDS, the effect is SPECIFIC
    to the dominant set (not "any ablation hurts");
  * keep ONLY the top-k frequencies         -> if accuracy HOLDS, they are SUFFICIENT.

No training: everything is FFT-filtering the saved weights + forward passes, CPU
in seconds. Honest-measurement: ``status == "pass"`` IFF validly measured (the
checkpoint loads and generalizes, the random control ran); the verdict reports
how causal the dependence actually is, including an honest "no dependence" null.
"""

from __future__ import annotations

import copy
import random

import torch

from minigpt.experiment_utils import mean_std
from minigpt.grok_checkpoint_v1185 import CheckpointMeta
from minigpt.grok_interp_v1188 import concentration_metrics, embedding_spectrum, number_embedding
from minigpt.grok_predict_v1186 import evaluate_table
from minigpt.model import MiniGPT
from minigpt.report_utils import utc_now


def filter_embedding(E: torch.Tensor, folded_freqs, mode: str, p: int) -> torch.Tensor:
    """Return ``E`` (a ``(p, n_embd)`` number-embedding) with frequencies filtered
    along the number axis. ``folded_freqs`` are rFFT indices in ``1..p//2``.
    ``mode="remove"`` zeroes those frequencies; ``mode="keep"`` zeroes every
    non-DC frequency EXCEPT those (DC is always retained)."""
    spectrum = torch.fft.rfft(E, dim=0)  # (p//2 + 1, n_embd)
    target = {int(k) for k in folded_freqs}
    for k in range(1, spectrum.shape[0]):  # never touch DC (k=0)
        drop = (k in target) if mode == "remove" else (k not in target)
        if drop:
            spectrum[k] = 0
    return torch.fft.irfft(spectrum, n=p, dim=0).to(E.dtype)


def ablated_model(model: MiniGPT, p: int, folded_freqs, mode: str) -> MiniGPT:
    """A deep copy of ``model`` whose number-embedding rows have been frequency
    filtered (the tied lm_head follows automatically). Op tokens are untouched."""
    clone = copy.deepcopy(model)
    weight = clone.token_embedding.weight
    filtered = filter_embedding(weight.detach()[:p].float(), folded_freqs, mode, p)
    with torch.no_grad():
        weight[:p] = filtered.to(weight.dtype).to(weight.device)
    return clone


def dominant_folded_freqs(model: MiniGPT, p: int, k: int) -> list[int]:
    """The top-k Fourier frequencies of the number-embedding (folded, 1-indexed)."""
    return concentration_metrics(embedding_spectrum(number_embedding(model, p)), top_k=k)["top_freqs"]


def _heldout(model: MiniGPT, meta: CheckpointMeta) -> float:
    return evaluate_table(model, meta)["heldout_acc"]


def run_ablation(
    model: MiniGPT,
    meta: CheckpointMeta,
    *,
    k: int = 5,
    random_trials: int = 5,
    random_seed: int = 0,
) -> dict:
    """Baseline + the three interventions. Random-control frequencies are drawn
    from the non-dominant set across ``random_trials`` seeds for a mean±std."""
    p = meta.p
    baseline = _heldout(model, meta)
    dominant = dominant_folded_freqs(model, p, k)

    acc_remove_dominant = _heldout(ablated_model(model, p, dominant, "remove"), meta)
    acc_keep_dominant = _heldout(ablated_model(model, p, dominant, "keep"), meta)

    non_dominant = [f for f in range(1, p // 2 + 1) if f not in set(dominant)]
    rng = random.Random(random_seed)
    random_accs = []
    for _ in range(random_trials):
        pick = rng.sample(non_dominant, min(k, len(non_dominant)))
        random_accs.append(_heldout(ablated_model(model, p, pick, "remove"), meta))
    rand_mean, rand_std = mean_std(random_accs)

    return {
        "p": p,
        "k": k,
        "dominant_freqs": dominant,
        "baseline_acc": round(baseline, 6),
        "acc_remove_dominant": round(acc_remove_dominant, 6),
        "acc_remove_random_mean": round(rand_mean, 6),
        "acc_remove_random_std": round(rand_std, 6),
        "acc_keep_dominant": round(acc_keep_dominant, 6),
        "random_trials": random_trials,
        "chance": round(1.0 / p, 6),
    }


def decide(
    result: dict,
    *,
    collapse_drop: float = 0.40,
    partial_drop: float = 0.15,
    specific_tol: float = 0.10,
    specificity_margin: float = 0.20,
    sufficient_min: float = 0.80,
) -> dict:
    """Validity gate + the causal verdict.

    Three orthogonal signals (NOT collapsed into a single threshold, which would
    under-claim a strong-but-redundant effect):
      * specific  -- removing random frequencies barely hurts AND removing the
                     dominant ones hurts much more (drop gap >= specificity_margin).
      * sufficient -- keeping ONLY the dominant frequencies retains accuracy.
      * necessity  -- full_collapse (drop >= collapse_drop) vs partial (>= partial_drop).
                     A model with redundancy can be specific+sufficient yet only
                     partially degrade on removal — that is still strongly causal.

    Gates: g0 the checkpoint generalizes (baseline >= 0.90) and the random control ran.
    ``status == pass`` IFF g0. The verdict reports HOW causal, honestly.
    """
    base = result["baseline_acc"]
    g0 = base >= 0.90 and result["random_trials"] > 0
    status = "pass" if g0 else "review"

    drop_dominant = base - result["acc_remove_dominant"]
    drop_random = base - result["acc_remove_random_mean"]
    specific = (drop_random <= specific_tol) and ((drop_dominant - drop_random) >= specificity_margin)
    sufficient = result["acc_keep_dominant"] >= sufficient_min
    full_collapse = drop_dominant >= collapse_drop
    partial_necessity = drop_dominant >= partial_drop

    if not specific and not sufficient:
        verdict = "no_clean_causal_frequency_dependence"
    elif specific and sufficient and full_collapse:
        verdict = "dominant_frequencies_causally_necessary_and_sufficient"
    elif specific and sufficient:
        # removing them is specifically damaging AND keeping only them suffices,
        # but redundancy means removal alone does not collapse to chance.
        verdict = "dominant_frequencies_sufficient_and_specific_partial_necessity"
    elif specific:
        verdict = "dominant_frequencies_causally_implicated_not_sufficient"
    else:  # sufficient but not specific
        verdict = "dominant_frequencies_sufficient_not_specific"

    return {
        "status": status,
        "verdict": verdict,
        "g0_checkpoint_generalizes": g0,
        "drop_dominant": round(drop_dominant, 6),
        "drop_random": round(drop_random, 6),
        "specific": specific,
        "sufficient": sufficient,
        "full_collapse": full_collapse,
        "partial_necessity": partial_necessity,
    }


def build_report(result: dict, info: dict, checkpoint_path: str, generated_at: str | None = None) -> dict:
    rows = [
        {"intervention": "baseline", "heldout_acc": result["baseline_acc"], "note": "no ablation"},
        {"intervention": "remove_dominant", "heldout_acc": result["acc_remove_dominant"],
         "note": f"removed top-{result['k']} freqs {result['dominant_freqs']}"},
        {"intervention": "remove_random", "heldout_acc": result["acc_remove_random_mean"],
         "note": f"mean over {result['random_trials']} random non-dominant {result['k']}-freq removals (std {result['acc_remove_random_std']})"},
        {"intervention": "keep_only_dominant", "heldout_acc": result["acc_keep_dominant"],
         "note": f"kept only top-{result['k']} freqs (+DC)"},
    ]
    summary = {
        "checkpoint": checkpoint_path,
        "p": result["p"],
        "k": result["k"],
        "dominant_freqs": result["dominant_freqs"],
        "baseline_acc": result["baseline_acc"],
        "acc_remove_dominant": result["acc_remove_dominant"],
        "acc_remove_random_mean": result["acc_remove_random_mean"],
        "acc_keep_dominant": result["acc_keep_dominant"],
        "chance": result["chance"],
        "drop_dominant": info["drop_dominant"],
        "drop_random": info["drop_random"],
        "specific": info["specific"],
        "sufficient": info["sufficient"],
        "full_collapse": info["full_collapse"],
        "partial_necessity": info["partial_necessity"],
        "verdict": info["verdict"],
        "boundary": "toy_scale_single_checkpoint_causal_frequency_ablation_not_a_general_interpretability_claim",
    }
    return {
        "schema_version": 1,
        "title": "MiniGPT v1191 grokking causal frequency ablation",
        "generated_at": generated_at or utc_now(),
        "status": info["status"],
        "decision": info["verdict"],
        "summary": summary,
        "rows": rows,
        "recommendations": _recommendations(info, result),
        "csv_fieldnames": ["intervention", "heldout_acc", "note"],
    }


def _recommendations(info: dict, result: dict) -> list[str]:
    v = info["verdict"]
    base, rd, rr, kd = (result["baseline_acc"], result["acc_remove_dominant"],
                        result["acc_remove_random_mean"], result["acc_keep_dominant"])
    if v == "dominant_frequencies_causally_necessary_and_sufficient":
        return [
            f"Causal: removing the top-{result['k']} frequencies {result['dominant_freqs']} collapses held-out accuracy {base:.3f} -> {rd:.3f}, removing random frequencies barely hurts ({rr:.3f}), and keeping ONLY them retains {kd:.3f}.",
            "This upgrades the v1188/v1190 correlational Fourier evidence to a causal mechanism for modular addition.",
        ]
    if v == "dominant_frequencies_sufficient_and_specific_partial_necessity":
        return [
            f"Strongly causal but redundant: keeping ONLY the top-{result['k']} frequencies {result['dominant_freqs']} retains held-out accuracy {kd:.3f} (SUFFICIENT), and removing them is specifically damaging ({base:.3f} -> {rd:.3f}) vs removing random frequencies ({rr:.3f}).",
            f"Removal does not collapse to chance ({rd:.3f}), so the dominant frequencies carry the addition algorithm but the model has redundancy — honest partial necessity, not total necessity.",
            "This still upgrades v1188/v1190 from correlation to causation: the dominant Fourier frequencies are where the algorithm lives.",
        ]
    if v == "dominant_frequencies_causally_implicated_not_sufficient":
        return ["Removing the dominant frequencies is specifically damaging (random removal is not), but keeping only them does not retain accuracy — necessary-ish, not sufficient."]
    if v == "dominant_frequencies_sufficient_not_specific":
        return ["Keeping only the dominant frequencies suffices, but removing random frequencies hurts as much as removing the dominant ones — not a specific dependence."]
    return ["Neither specificity nor sufficiency held — no clean causal frequency dependence (honest null); the structure may be redundant or distributed."]


__all__ = [
    "filter_embedding", "ablated_model", "dominant_folded_freqs",
    "run_ablation", "decide", "build_report",
]
