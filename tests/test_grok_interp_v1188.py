"""Tests for v1188 grokking mechanistic interpretability.

Fast and CPU-only: the FFT spectrum + concentration metrics on synthetic
embeddings (a pure cosine must give one dominant frequency; random must be
diffuse), the decide() verdict ladder on synthetic arm metrics, and a tiny
end-to-end smoke.
"""

from __future__ import annotations

import math

import torch

from minigpt.grok_interp_v1188 import (
    analyze_model,
    collect_arms,
    concentration_metrics,
    decide,
    embedding_spectrum,
)
from minigpt.grok_v1179 import GrokConfig, make_grok_model


def test_pure_cosine_embedding_has_one_dominant_frequency():
    p, n_embd = 97, 16
    n = torch.arange(p).float()
    freq = 7
    col = torch.cos(2 * math.pi * freq * n / p)
    E = col.unsqueeze(1).repeat(1, n_embd)  # every dim is the same freq-7 cosine
    spectrum = embedding_spectrum(E)
    metrics = concentration_metrics(spectrum)
    assert metrics["dominant_freq"] == freq
    assert metrics["top_k_fraction"] > 0.95  # nearly all power in one frequency
    assert metrics["spectral_entropy"] < 0.2


def test_random_embedding_is_diffuse():
    torch.manual_seed(0)
    E = torch.randn(97, 64)
    metrics = concentration_metrics(embedding_spectrum(E))
    # diffuse: top-5 of 48 freqs is far from concentrated, entropy near 1
    assert metrics["top_k_fraction"] < 0.5
    assert metrics["spectral_entropy"] > 0.7


def test_analyze_model_returns_spectrum_and_metrics():
    model = make_grok_model(97 + 2, GrokConfig(p=97, n_embd=32))
    out = analyze_model(model, 97)
    assert len(out["spectrum"]) == 97 // 2  # p//2+1 minus the dropped DC term
    assert 0.0 <= out["top_k_fraction"] <= 1.0
    assert out["dominant_freq"] >= 1


# --------------------------------------------------------------------------
# decide() verdict ladder on synthetic arm metrics
# --------------------------------------------------------------------------
def _arm(fracs, entropies, *, grokked, memorized):
    return [
        {"top_k_fraction": f, "spectral_entropy": e, "grokked": grokked, "memorized": memorized,
         "seed": i, "dominant_freq": 7, "n_freqs_for_90pct": 3}
        for i, (f, e) in enumerate(zip(fracs, entropies))
    ]


def test_verdict_structure_explains_generalization():
    arms = {
        "grokked": _arm([0.70, 0.72, 0.68], [0.20, 0.22, 0.18], grokked=True, memorized=True),
        "memorized": _arm([0.18, 0.20, 0.16], [0.92, 0.90, 0.93], grokked=False, memorized=True),
        "random": _arm([0.12, 0.13, 0.11], [0.98, 0.97, 0.99], grokked=False, memorized=False),
    }
    out = decide(arms)
    assert out["status"] == "pass"
    assert out["verdict"] == "fourier_structure_explains_generalization"


def test_verdict_from_training_not_generalization():
    # grokked beats random but is indistinguishable from memorized
    arms = {
        "grokked": _arm([0.60, 0.62, 0.58], [0.30] * 3, grokked=True, memorized=True),
        "memorized": _arm([0.59, 0.61, 0.57], [0.31] * 3, grokked=False, memorized=True),
        "random": _arm([0.12, 0.13, 0.11], [0.98] * 3, grokked=False, memorized=False),
    }
    out = decide(arms)
    assert out["verdict"] == "fourier_structure_from_training_not_generalization"


def test_verdict_not_separable_from_random():
    arms = {
        "grokked": _arm([0.14, 0.15, 0.13], [0.95] * 3, grokked=True, memorized=True),
        "memorized": _arm([0.14, 0.13, 0.15], [0.96] * 3, grokked=False, memorized=True),
        "random": _arm([0.13, 0.14, 0.12], [0.97] * 3, grokked=False, memorized=False),
    }
    out = decide(arms)
    assert out["verdict"] == "fourier_structure_not_separable"


def test_status_review_when_arm_misbehaves():
    # a "grokked" arm that did not grok invalidates the contrast
    arms = {
        "grokked": _arm([0.70] * 3, [0.20] * 3, grokked=False, memorized=True),
        "memorized": _arm([0.18] * 3, [0.92] * 3, grokked=False, memorized=True),
        "random": _arm([0.12] * 3, [0.98] * 3, grokked=False, memorized=False),
    }
    out = decide(arms)
    assert out["gates"]["g0_arms_behaved"] is False
    assert out["status"] == "review"


# --------------------------------------------------------------------------
# tiny end-to-end smoke (CPU): trains real arms and analyzes their spectra
# --------------------------------------------------------------------------
def test_smoke_collect_and_decide():
    arms = collect_arms(
        p=5, seeds=(0,), train_frac=0.4, device=torch.device("cpu"),
        memorize_steps=150, grok_max_steps=300,
    )
    assert set(arms) == {"grokked", "memorized", "random"}
    for name in arms:
        assert len(arms[name]) == 1
        assert "top_k_fraction" in arms[name][0]
    out = decide(arms)
    assert out["status"] in {"pass", "review"}
    assert out["verdict"].startswith("fourier_structure")
