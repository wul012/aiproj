"""Tests for v1185 canonical grokking checkpoint.

Fast and CPU-only: the save/load round-trip (the key correctness guard), meta
reconstruction, held-out demo decoding, the verdict ladder on synthetic metadata,
and training determinism.
"""

from __future__ import annotations

import torch

from minigpt.grok_checkpoint_v1185 import (
    CheckpointMeta,
    build_report,
    evaluate_generalization,
    load_checkpoint,
    logits_match,
    save_checkpoint,
    train_to_grok,
)
from minigpt.grok_v1179 import GrokConfig


def _tiny_config():
    return GrokConfig(
        p=5, train_frac=0.4, n_layer=1, n_head=4, n_embd=16,
        max_steps=300, eval_every=100, seeds=(0,), wds=(1.0,),
    )


def _meta(*, t_mem=100, t_gen=5000, final_train=1.0, final_val=0.96):
    return CheckpointMeta(
        p=97, train_frac=0.2, seed=1337, weight_decay=1.0, vocab_size=99,
        n_layer=1, n_head=4, n_embd=128, block_size=5,
        t_mem=t_mem, t_gen=t_gen, final_train_acc=final_train, final_val_acc=final_val, steps_run=5000,
    )


def _demo(heldout_acc=0.96):
    return {"heldout_acc": heldout_acc, "n_heldout": 100,
            "samples": [{"a": 1, "b": 2, "predicted": 3, "truth": 3, "correct": True}]}


# --------------------------------------------------------------------------
# save / load round-trip — the key correctness guard
# --------------------------------------------------------------------------
def test_checkpoint_roundtrips_to_identical_logits(tmp_path):
    device = torch.device("cpu")
    model, meta, _ = train_to_grok(_tiny_config(), device)
    path = tmp_path / "ckpt.pt"
    save_checkpoint(model, meta, path)
    reloaded, reloaded_meta = load_checkpoint(path, device=device)
    assert logits_match(model, reloaded, meta.p)  # bit-identical reload
    assert reloaded_meta.p == 5 and reloaded_meta.vocab_size == 7 and reloaded_meta.n_embd == 16


def test_loaded_checkpoint_is_self_contained(tmp_path):
    # load_checkpoint must rebuild the architecture purely from the embedded meta
    model, meta, _ = train_to_grok(_tiny_config(), torch.device("cpu"))
    path = tmp_path / "ckpt.pt"
    save_checkpoint(model, meta, path)
    reloaded, _ = load_checkpoint(path)  # no config passed in
    data = torch.zeros(1, 5, dtype=torch.long)
    logits, _ = reloaded(data)
    assert logits.shape == (1, 5, 7)


# --------------------------------------------------------------------------
# held-out demo decoding
# --------------------------------------------------------------------------
def test_evaluate_generalization_decodes_and_scores_heldout():
    model, meta, _ = train_to_grok(_tiny_config(), torch.device("cpu"))
    demo = evaluate_generalization(model, meta, torch.device("cpu"), n_samples=5)
    assert 0.0 <= demo["heldout_acc"] <= 1.0
    assert demo["n_heldout"] > 0
    for s in demo["samples"]:
        assert s["truth"] == (s["a"] + s["b"]) % meta.p  # decoding targets the true modular sum
        assert s["correct"] == (s["predicted"] == s["truth"])


# --------------------------------------------------------------------------
# verdict ladder on synthetic metadata
# --------------------------------------------------------------------------
def test_verdict_ready_when_grokked_roundtrip_and_strong_heldout():
    report = build_report(_meta(), [], _demo(0.96), roundtrip_ok=True, generated_at="x")
    assert report["status"] == "pass"
    assert report["decision"] == "canonical_grokking_checkpoint_ready"
    assert report["summary"]["grok_delay_steps"] == 4900


def test_verdict_memorized_but_did_not_grok():
    report = build_report(_meta(t_gen=None), [], _demo(0.5), roundtrip_ok=True, generated_at="x")
    assert report["status"] == "review"
    assert report["decision"] == "checkpoint_memorized_but_did_not_grok"


def test_verdict_roundtrip_mismatch():
    report = build_report(_meta(), [], _demo(0.96), roundtrip_ok=False, generated_at="x")
    assert report["decision"] == "checkpoint_grokked_but_roundtrip_mismatch"


def test_verdict_weak_heldout():
    report = build_report(_meta(), [], _demo(0.4), roundtrip_ok=True, generated_at="x")
    assert report["decision"] == "checkpoint_grokked_but_weak_heldout"


def test_verdict_failed_to_memorize():
    report = build_report(_meta(t_mem=None, t_gen=None, final_train=0.3), [], _demo(0.1),
                          roundtrip_ok=True, generated_at="x")
    assert report["decision"] == "checkpoint_failed_to_memorize"


# --------------------------------------------------------------------------
# determinism
# --------------------------------------------------------------------------
def test_train_to_grok_is_deterministic():
    a_model, a_meta, _ = train_to_grok(_tiny_config(), torch.device("cpu"))
    b_model, b_meta, _ = train_to_grok(_tiny_config(), torch.device("cpu"))
    assert a_meta.as_dict() == b_meta.as_dict()
    assert logits_match(a_model, b_model, a_meta.p)
