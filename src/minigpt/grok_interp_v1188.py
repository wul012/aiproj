"""v1188: mechanistic interpretability of the grokked modular-addition model.

A new axis for the project: instead of measuring *that* the model generalizes
(v1179) or shipping it (v1185), v1188 reverse-engineers *how* it computes
``a + b (mod p)``. The canonical result (Nanda 2023) is that a grokked
modular-addition network represents each number as a sparse set of Fourier
features (a handful of key frequencies) and combines them via trig identities.

The falsifiable signature lives in the token embeddings: viewed as functions of
the number ``0..p-1``, the embedding columns of a grokked model should have power
concentrated in a FEW frequencies (a sparse FFT), whereas a random-init model is
diffuse. The scientifically meaningful comparison is the paired one: a
*memorized-but-not-grokked* model (weight_decay=0, same init+split) should NOT
develop the structure — tying the Fourier mechanism to GENERALIZATION, not merely
to training. This is the weight-level explanation of the v1179/v1183 behavior.

Almost free: the grokked structure is read straight off saved/quickly-trained
weights (no long sweeps). Honest-measurement contract: ``status == "pass"`` IFF
validly measured — every "grokked" arm actually grokked, every "memorized" arm
memorized-without-grokking, and the seed grid is complete. The verdict reports
whether the Fourier structure is present and whether it tracks generalization.
"""

from __future__ import annotations

import torch

from minigpt.experiment_utils import mean_std, significant
from minigpt.grok_checkpoint_v1185 import load_checkpoint, train_to_grok
from minigpt.grok_predict_v1186 import DEFAULT_CHECKPOINT
from minigpt.grok_v1179 import GrokConfig, make_grok_model
from minigpt.report_utils import utc_now
from minigpt.script_runtime import seed_everything

TOP_K = 5  # number of leading frequencies for the concentration metric


def number_embedding(model, p: int) -> torch.Tensor:
    """The token-embedding rows for the numbers ``0..p-1`` as a ``(p, n_embd)``
    tensor on CPU (the op tokens PLUS/EQ at indices p, p+1 are excluded)."""
    return model.token_embedding.weight.detach().cpu()[:p].float()


def embedding_spectrum(E: torch.Tensor) -> torch.Tensor:
    """Normalized power per non-DC frequency: rFFT each embedding column over the
    number axis, sum power across dimensions, drop the DC term, normalize to 1."""
    spectrum = torch.fft.rfft(E, dim=0)            # (p//2 + 1, n_embd) complex
    power = (spectrum.abs() ** 2).sum(dim=1)        # (p//2 + 1,)
    power = power[1:]                               # drop DC (the per-column mean)
    total = power.sum()
    return power / total if float(total) > 0 else power


def concentration_metrics(norm_power: torch.Tensor, top_k: int = TOP_K) -> dict:
    """How concentrated the (already-normalized) spectrum is. Sparse Fourier
    structure -> high ``top_k_fraction``, low ``spectral_entropy``."""
    values, idx = torch.sort(norm_power, descending=True)
    top_k_fraction = float(values[:top_k].sum())
    probs = norm_power.clamp_min(1e-12)
    n = probs.numel()
    spectral_entropy = float(-(probs * probs.log()).sum() / torch.log(torch.tensor(float(n))))
    cumulative = torch.cumsum(values, dim=0)
    n_freqs_for_90pct = int((cumulative < 0.90).sum().item()) + 1
    return {
        "top_k_fraction": round(top_k_fraction, 6),
        "spectral_entropy": round(spectral_entropy, 6),
        "dominant_freq": int(idx[0].item()) + 1,  # +1 because DC was dropped
        "n_freqs_for_90pct": n_freqs_for_90pct,
        "top_freqs": [int(i.item()) + 1 for i in idx[:top_k]],
    }


def analyze_model(model, p: int) -> dict:
    """Spectrum-concentration metrics for one model's number embeddings."""
    spectrum = embedding_spectrum(number_embedding(model, p))
    metrics = concentration_metrics(spectrum)
    metrics["spectrum"] = [round(float(x), 6) for x in spectrum.tolist()]
    return metrics


def _grok_config(seed: int, p: int, train_frac: float, weight_decay: float, max_steps: int) -> GrokConfig:
    return GrokConfig(p=p, train_frac=train_frac, seeds=(seed,), wds=(weight_decay,), max_steps=max_steps)


def collect_arms(
    *,
    p: int,
    seeds: tuple[int, ...],
    train_frac: float,
    device: torch.device,
    memorize_steps: int,
    grok_max_steps: int,
) -> dict:
    """For each seed, train a grokked (wd=1) and a paired memorized (wd=0) model
    and build a random-init null, recording each one's spectrum concentration plus
    whether the arm reached the expected behavior (grok / memorize-only)."""
    arms: dict[str, list[dict]] = {"grokked": [], "memorized": [], "random": []}
    for seed in seeds:
        grok_model, grok_meta, _ = train_to_grok(
            _grok_config(seed, p, train_frac, 1.0, grok_max_steps), device
        )
        mem_model, mem_meta, _ = train_to_grok(
            _grok_config(seed, p, train_frac, 0.0, memorize_steps), device
        )
        seed_everything(seed)
        rand_model = make_grok_model(p + 2, _grok_config(seed, p, train_frac, 0.0, 0)).to(device)

        g = analyze_model(grok_model, p)
        g.update(seed=seed, grokked=grok_meta.t_gen is not None, memorized=grok_meta.t_mem is not None,
                 final_val_acc=grok_meta.final_val_acc)
        m = analyze_model(mem_model, p)
        m.update(seed=seed, grokked=mem_meta.t_gen is not None, memorized=mem_meta.t_mem is not None,
                 final_val_acc=mem_meta.final_val_acc)
        r = analyze_model(rand_model, p)
        r.update(seed=seed, grokked=False, memorized=False, final_val_acc=None)
        arms["grokked"].append(g)
        arms["memorized"].append(m)
        arms["random"].append(r)
    return arms


def decide(arms: dict) -> dict:
    """Validity gates + the Fourier-structure verdict.

    Gates (validity, not flattery):
      g0_arms_behaved   -- every grokked arm grokked AND every memorized arm
                           memorized-without-grokking (else the contrast is invalid).
      g1_grid_complete  -- equal, non-empty seed counts across the three arms.
    ``status == pass`` IFF g0 and g1.

    Verdict:
      fourier_structure_explains_generalization -- grokked concentration significantly
          exceeds BOTH random and memorized (structure tracks generalization).
      fourier_structure_from_training_not_generalization -- grokked > random but
          ~ memorized (training builds structure regardless of generalization).
      fourier_structure_not_separable -- grokked not significantly above random.
    """
    def stat(name, key):
        return mean_std([row[key] for row in arms[name]])

    g_mean, g_std = stat("grokked", "top_k_fraction")
    m_mean, m_std = stat("memorized", "top_k_fraction")
    r_mean, r_std = stat("random", "top_k_fraction")
    ge_mean, _ = stat("grokked", "spectral_entropy")
    me_mean, _ = stat("memorized", "spectral_entropy")
    re_mean, _ = stat("random", "spectral_entropy")

    n = len(arms["grokked"])
    g0_arms_behaved = (
        n > 0
        and all(row["grokked"] for row in arms["grokked"])
        and all(row["memorized"] and not row["grokked"] for row in arms["memorized"])
    )
    g1_grid_complete = len({len(arms[name]) for name in ("grokked", "memorized", "random")}) == 1 and n > 0
    status = "pass" if (g0_arms_behaved and g1_grid_complete) else "review"

    beats_random = significant(g_mean, g_std, r_mean, r_std)
    beats_memorized = significant(g_mean, g_std, m_mean, m_std)
    if beats_random and beats_memorized:
        verdict = "fourier_structure_explains_generalization"
    elif beats_random:
        verdict = "fourier_structure_from_training_not_generalization"
    else:
        verdict = "fourier_structure_not_separable"

    return {
        "status": status,
        "verdict": verdict,
        "gates": {"g0_arms_behaved": g0_arms_behaved, "g1_grid_complete": g1_grid_complete},
        "grokked_top_k_fraction": (round(g_mean, 6), round(g_std, 6)),
        "memorized_top_k_fraction": (round(m_mean, 6), round(m_std, 6)),
        "random_top_k_fraction": (round(r_mean, 6), round(r_std, 6)),
        "grokked_entropy_mean": round(ge_mean, 6),
        "memorized_entropy_mean": round(me_mean, 6),
        "random_entropy_mean": round(re_mean, 6),
        "beats_random": beats_random,
        "beats_memorized": beats_memorized,
    }


def analyze_shipped_checkpoint(p: int, device: torch.device) -> dict | None:
    """Concentration metrics for the committed v1185 grokked checkpoint, if present
    — a tie-in that the *shipped* model carries the Fourier structure."""
    if not DEFAULT_CHECKPOINT.exists():
        return None
    model, meta = load_checkpoint(DEFAULT_CHECKPOINT, device=device)
    metrics = analyze_model(model, meta.p)
    metrics.update(seed=meta.seed, source="v1185_shipped_checkpoint", final_val_acc=meta.final_val_acc)
    return metrics


def build_report(arms: dict, info: dict, shipped: dict | None, p: int, generated_at: str | None = None) -> dict:
    rows = []
    for name in ("grokked", "memorized", "random"):
        for row in arms[name]:
            rows.append({
                "arm": name, "seed": row["seed"], "top_k_fraction": row["top_k_fraction"],
                "spectral_entropy": row["spectral_entropy"], "dominant_freq": row["dominant_freq"],
                "n_freqs_for_90pct": row["n_freqs_for_90pct"],
            })
    summary = {
        "p": p,
        "top_k": TOP_K,
        "seeds": len(arms["grokked"]),
        "verdict": info["verdict"],
        "g0_arms_behaved": info["gates"]["g0_arms_behaved"],
        "g1_grid_complete": info["gates"]["g1_grid_complete"],
        "grokked_top_k_fraction": info["grokked_top_k_fraction"],
        "memorized_top_k_fraction": info["memorized_top_k_fraction"],
        "random_top_k_fraction": info["random_top_k_fraction"],
        "grokked_entropy_mean": info["grokked_entropy_mean"],
        "memorized_entropy_mean": info["memorized_entropy_mean"],
        "random_entropy_mean": info["random_entropy_mean"],
        "beats_random": info["beats_random"],
        "beats_memorized": info["beats_memorized"],
        "shipped_checkpoint_top_k_fraction": (shipped["top_k_fraction"] if shipped else None),
        "shipped_checkpoint_dominant_freq": (shipped["dominant_freq"] if shipped else None),
        "boundary": "toy_scale_single_task_interpretability_embedding_fourier_structure_only",
    }
    return {
        "schema_version": 1,
        "title": "MiniGPT v1188 grokking mechanistic interpretability",
        "generated_at": generated_at or utc_now(),
        "status": info["status"],
        "decision": info["verdict"],
        "summary": summary,
        "rows": rows,
        "spectra": {name: [row["spectrum"] for row in arms[name]] for name in arms},
        "shipped_checkpoint": shipped,
        "recommendations": _recommendations(info),
        "csv_fieldnames": ["arm", "seed", "top_k_fraction", "spectral_entropy", "dominant_freq", "n_freqs_for_90pct"],
    }


def _recommendations(info: dict) -> list[str]:
    v = info["verdict"]
    if v == "fourier_structure_explains_generalization":
        return [
            "The grokked model's number embeddings are sparse in the Fourier basis (a few dominant frequencies), significantly more than both a random-init and a memorized-but-not-grokked model.",
            "This is the weight-level mechanism behind grokking: only the generalizing (weight-decayed) model develops the Fourier structure that implements modular addition via trig identities.",
        ]
    if v == "fourier_structure_from_training_not_generalization":
        return ["Trained models are more Fourier-concentrated than random init, but the grokked and memorized models are not separable — at this scale the structure tracks training, not specifically generalization."]
    return ["The grokked model's embedding spectrum is not significantly more concentrated than random init — the Fourier-structure hypothesis is not supported here (honest null)."]


__all__ = [
    "TOP_K", "number_embedding", "embedding_spectrum", "concentration_metrics",
    "analyze_model", "collect_arms", "decide", "analyze_shipped_checkpoint", "build_report",
]
