"""Tests for v1191 causal frequency ablation.

CPU-only and fast: the FFT filter (remove vs keep a frequency), the tied-row
preservation, the decide() verdict ladder on synthetic accuracies, and a tiny
end-to-end smoke that run_ablation produces the expected keys.
"""

from __future__ import annotations

import math

import torch

from minigpt.grok_checkpoint_v1185 import CheckpointMeta
from minigpt.grok_freq_ablation_v1191 import (
    ablated_model,
    build_report,
    decide,
    filter_embedding,
    run_ablation,
)
from minigpt.grok_interp_v1188 import concentration_metrics, embedding_spectrum
from minigpt.grok_v1179 import GrokConfig, make_grok_model


def test_filter_remove_zeroes_the_named_frequency():
    p, n_embd = 97, 8
    n = torch.arange(p).float()
    E = (torch.cos(2 * math.pi * 7 * n / p) + 0.5 * torch.cos(2 * math.pi * 13 * n / p)).unsqueeze(1).repeat(1, n_embd)
    removed = filter_embedding(E, [7], "remove", p)
    spec = embedding_spectrum(removed)
    # after removing freq 7, the dominant remaining frequency must be 13
    assert concentration_metrics(spec)["dominant_freq"] == 13


def test_filter_keep_only_retains_one_frequency():
    p, n_embd = 97, 8
    n = torch.arange(p).float()
    E = torch.randn(p, n_embd) + torch.cos(2 * math.pi * 5 * n / p).unsqueeze(1)
    kept = filter_embedding(E, [5], "keep", p)
    metrics = concentration_metrics(embedding_spectrum(kept))
    assert metrics["dominant_freq"] == 5
    assert metrics["top_k_fraction"] > 0.95  # essentially all non-DC power at freq 5


def test_ablated_model_preserves_op_token_rows():
    p = 97
    model = make_grok_model(p + 2, GrokConfig(p=p, n_embd=32))
    before = model.token_embedding.weight.detach().clone()
    clone = ablated_model(model, p, [3, 7], "remove")
    after = clone.token_embedding.weight.detach()
    assert torch.allclose(after[p:], before[p:])          # PLUS/EQ rows untouched
    assert not torch.allclose(after[:p], before[:p])       # number rows changed
    assert torch.allclose(model.token_embedding.weight.detach(), before)  # original intact


# --------------------------------------------------------------------------
# decide() verdict ladder
# --------------------------------------------------------------------------
def _result(*, base=0.966, remove_dom=0.05, remove_rand=0.94, keep_dom=0.93):
    return {
        "p": 97, "k": 5, "dominant_freqs": [43, 3, 48, 26, 44],
        "baseline_acc": base, "acc_remove_dominant": remove_dom,
        "acc_remove_random_mean": remove_rand, "acc_remove_random_std": 0.01,
        "acc_keep_dominant": keep_dom, "random_trials": 5, "chance": 1 / 97,
    }


def test_verdict_necessary_and_sufficient():
    out = decide(_result())  # remove collapses to 0.05, random fine, keep retains
    assert out["status"] == "pass"
    assert out["verdict"] == "dominant_frequencies_causally_necessary_and_sufficient"


def test_verdict_sufficient_and_specific_partial_necessity():
    # the real v1191 result: specific + sufficient, but removal only partially degrades
    out = decide(_result(remove_dom=0.578, remove_rand=0.973, keep_dom=0.972))
    assert out["specific"] is True and out["sufficient"] is True
    assert out["full_collapse"] is False
    assert out["verdict"] == "dominant_frequencies_sufficient_and_specific_partial_necessity"


def test_verdict_implicated_not_sufficient():
    out = decide(_result(remove_dom=0.05, keep_dom=0.40))  # collapse + specific, keep-only fails
    assert out["verdict"] == "dominant_frequencies_causally_implicated_not_sufficient"


def test_verdict_sufficient_not_specific():
    out = decide(_result(remove_rand=0.40, keep_dom=0.93))  # random also hurts -> not specific
    assert out["verdict"] == "dominant_frequencies_sufficient_not_specific"


def test_verdict_no_clean_dependence():
    out = decide(_result(remove_dom=0.92, keep_dom=0.30))  # removal barely hurts, keep doesn't retain
    assert out["verdict"] == "no_clean_causal_frequency_dependence"


def test_status_review_when_checkpoint_does_not_generalize():
    out = decide(_result(base=0.30, remove_dom=0.05))
    assert out["status"] == "review"


def test_build_report_shape():
    result = _result()
    report = build_report(result, decide(result), "ckpt.pt", generated_at="x")
    assert report["status"] == "pass"
    assert [r["intervention"] for r in report["rows"]] == [
        "baseline", "remove_dominant", "remove_random", "keep_only_dominant",
    ]


# --------------------------------------------------------------------------
# tiny end-to-end smoke (CPU): run_ablation plumbing on a small model
# --------------------------------------------------------------------------
def test_smoke_run_ablation_keys():
    p = 11
    model = make_grok_model(p + 2, GrokConfig(p=p, n_embd=16))
    meta = CheckpointMeta(
        p=p, train_frac=0.4, seed=0, weight_decay=1.0, vocab_size=p + 2,
        n_layer=1, n_head=4, n_embd=16, block_size=5,
        t_mem=1, t_gen=1, final_train_acc=1.0, final_val_acc=0.5, steps_run=1,
    )
    result = run_ablation(model, meta, k=3, random_trials=2)
    for key in ("baseline_acc", "acc_remove_dominant", "acc_remove_random_mean", "acc_keep_dominant"):
        assert 0.0 <= result[key] <= 1.0
    assert len(result["dominant_freqs"]) == 3
