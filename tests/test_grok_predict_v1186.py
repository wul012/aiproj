"""Tests for v1186 grokking checkpoint inference/demo.

CPU-only and fast: prompt encoding, the predict/predict_pairs plumbing on a tiny
model, the verdict ladder on synthetic metrics, and an integration test that
loads the SHIPPED v1185 checkpoint from disk and confirms it computes a+b mod 97.
"""

from __future__ import annotations

import pytest
import torch

from minigpt.grok_checkpoint_v1185 import CheckpointMeta
from minigpt.grok_predict_v1186 import (
    DEFAULT_CHECKPOINT,
    build_report,
    encode_problem,
    evaluate_table,
    load_default,
    predict,
    predict_pairs,
)
from minigpt.grok_v1179 import GrokConfig, make_grok_model


def test_encode_problem_is_the_four_token_prompt():
    x = encode_problem(36, 37, 97)
    assert x.shape == (1, 4)
    assert x.tolist() == [[36, 97, 37, 98]]  # [a, PLUS=p, b, EQ=p+1]


def test_predict_pairs_plumbing_on_tiny_model():
    model = make_grok_model(5 + 2, GrokConfig(p=5, n_embd=16))
    rows = predict_pairs(model, [(1, 2), (3, 4)], 5)
    for r in rows:
        assert r["truth"] == (r["a"] + r["b"]) % 5
        assert r["correct"] == (r["predicted"] == r["truth"])
        assert 0 <= r["predicted"] < 7  # within vocab


def test_predict_returns_valid_token_on_tiny_model():
    model = make_grok_model(5 + 2, GrokConfig(p=5, n_embd=16))
    out = predict(model, 2, 3, 5)
    assert isinstance(out, int) and 0 <= out < 7


# --------------------------------------------------------------------------
# verdict ladder
# --------------------------------------------------------------------------
def _meta():
    return CheckpointMeta(
        p=97, train_frac=0.2, seed=1337, weight_decay=1.0, vocab_size=99,
        n_layer=1, n_head=4, n_embd=128, block_size=5,
        t_mem=100, t_gen=11400, final_train_acc=1.0, final_val_acc=0.966, steps_run=11600,
    )


def _table(train=1.0, heldout=0.966):
    return {"p": 97, "overall_acc": 0.99, "train_acc": train, "heldout_acc": heldout,
            "n_total": 9409, "n_heldout": 7527, "n_heldout_correct": 7271}


def _rows(correct=True):
    return [{"a": 36, "b": 37, "predicted": 73 if correct else 0, "truth": 73, "correct": correct}]


def test_verdict_usable():
    r = build_report(_meta(), _table(), _rows(True), "ckpt.pt", generated_at="x")
    assert r["status"] == "pass"
    assert r["decision"] == "grokking_checkpoint_usable"


def test_verdict_weak_when_heldout_low():
    r = build_report(_meta(), _table(heldout=0.5), _rows(True), "ckpt.pt", generated_at="x")
    assert r["status"] == "review"
    assert r["decision"] == "checkpoint_loaded_but_weak"


def test_verdict_demo_pair_wrong():
    r = build_report(_meta(), _table(), _rows(False), "ckpt.pt", generated_at="x")
    assert r["decision"] == "checkpoint_usable_but_demo_pair_wrong"


# --------------------------------------------------------------------------
# integration: the SHIPPED checkpoint loads and computes a+b mod 97
# --------------------------------------------------------------------------
@pytest.mark.skipif(not DEFAULT_CHECKPOINT.exists(), reason="canonical v1185 checkpoint not present")
def test_shipped_checkpoint_loads_and_predicts():
    model, meta = load_default(device=torch.device("cpu"))
    assert meta.p == 97
    assert predict(model, 36, 37, meta.p) == 73  # (36+37) % 97
    assert predict(model, 96, 96, meta.p) == (96 + 96) % 97
    table = evaluate_table(model, meta)
    assert table["train_acc"] >= 0.99
    assert table["heldout_acc"] >= 0.90  # re-derives v1185's generalization from disk
