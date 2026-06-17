"""Tests for v1179 grokking (delayed generalization on modular arithmetic).

All CPU and fast: the task builder, the deterministic split, answer-token
loss/accuracy indexing, the censoring aggregator, the decide() verdict ladder on
synthetic metric inputs, and a tiny end-to-end smoke that the pipeline runs
deterministically and the model memorizes a small train set.
"""

from __future__ import annotations

import torch

from minigpt.grok_v1179 import (
    ANSWER_READ_POS,
    GrokConfig,
    SEQ_LEN,
    answer_accuracy,
    answer_loss,
    arm_aggregate,
    build_modular_task,
    decide,
    run_grok,
    split_indices,
    verify_task,
)


# --------------------------------------------------------------------------
# task correctness (g0)
# --------------------------------------------------------------------------
def test_modular_task_enumerates_all_pairs_correctly():
    p = 7
    data = build_modular_task(p)
    assert data.shape == (p * p, SEQ_LEN)
    a, plus, b, eq, c = (data[:, i] for i in range(SEQ_LEN))
    assert torch.equal(plus, torch.full_like(plus, p))
    assert torch.equal(eq, torch.full_like(eq, p + 1))
    assert torch.equal(c, (a + b) % p)
    # full enumeration: every (a, b) pair appears exactly once
    pairs = {(int(x), int(y)) for x, y in zip(a.tolist(), b.tolist())}
    assert len(pairs) == p * p
    assert verify_task(data, p) is True


def test_verify_task_rejects_corrupted_answers():
    p = 7
    data = build_modular_task(p)
    data[0, 4] = (int(data[0, 4]) + 1) % p  # break one answer
    assert verify_task(data, p) is False


# --------------------------------------------------------------------------
# deterministic disjoint split
# --------------------------------------------------------------------------
def test_split_is_deterministic_disjoint_and_sized():
    n = 97 * 97
    tr1, va1 = split_indices(n, 0.4, seed=1337)
    tr2, va2 = split_indices(n, 0.4, seed=1337)
    assert torch.equal(tr1, tr2) and torch.equal(va1, va2)  # deterministic
    assert len(tr1) + len(va1) == n
    assert abs(len(tr1) - round(0.4 * n)) <= 1
    assert set(tr1.tolist()).isdisjoint(set(va1.tolist()))  # disjoint
    # a different seed gives a different split
    tr3, _ = split_indices(n, 0.4, seed=1338)
    assert not torch.equal(tr1, tr3)


# --------------------------------------------------------------------------
# answer-token loss / accuracy index the EQ position -> answer token
# --------------------------------------------------------------------------
class _StubModel:
    def __init__(self, logits: torch.Tensor) -> None:
        self.logits = logits

    def eval(self) -> None:  # answer_accuracy calls model.eval()
        pass

    def __call__(self, batch: torch.Tensor):
        return self.logits, None


def test_answer_accuracy_reads_eq_position_and_answer_token():
    # rows: (1+2)%5=3, (0+1)%5=1  ;  vocab = p+2 = 7
    batch = torch.tensor([[1, 5, 2, 6, 3], [0, 5, 1, 6, 1]])
    logits = torch.zeros(2, SEQ_LEN, 7)
    logits[0, ANSWER_READ_POS, 3] = 10.0  # row 0 predicts c=3 correctly
    logits[1, ANSWER_READ_POS, 0] = 10.0  # row 1 predicts 0, target is 1 -> wrong
    model = _StubModel(logits)
    assert answer_accuracy(model, batch) == 0.5


def test_answer_loss_is_low_when_eq_position_predicts_the_answer():
    batch = torch.tensor([[1, 5, 2, 6, 3], [0, 5, 1, 6, 1]])
    correct = torch.zeros(2, SEQ_LEN, 7)
    correct[0, ANSWER_READ_POS, 3] = 20.0
    correct[1, ANSWER_READ_POS, 1] = 20.0
    wrong = torch.zeros(2, SEQ_LEN, 7)
    wrong[0, ANSWER_READ_POS, 0] = 20.0
    wrong[1, ANSWER_READ_POS, 0] = 20.0
    assert answer_loss(_StubModel(correct), batch).item() < 0.01
    assert answer_loss(_StubModel(wrong), batch).item() > 5.0


# --------------------------------------------------------------------------
# aggregation censors honestly
# --------------------------------------------------------------------------
def _result(*, grokked, memorized=True, t_mem=100, t_gen=5000, val_at_mem=0.02,
            final_train=1.0, final_val=1.0):
    return {
        "weight_decay": 1.0,
        "memorized": memorized,
        "grokked": grokked,
        "t_mem": t_mem if memorized else None,
        "t_gen": t_gen if grokked else None,
        "grok_gap": (t_gen - t_mem) if (grokked and memorized) else None,
        "val_at_mem": val_at_mem if grokked else None,
        "final_train_acc": final_train,
        "final_val_acc": final_val,
        "steps_run": 0,
        "curve": [],
    }


def test_arm_aggregate_averages_grok_step_only_over_grokked_seeds():
    results = [
        _result(grokked=True, t_gen=4000),
        _result(grokked=True, t_gen=5000),
        _result(grokked=True, t_gen=6000),
        _result(grokked=False),
        _result(grokked=False),
    ]
    agg = arm_aggregate(results)
    assert agg["n"] == 5 and agg["n_grokked"] == 3
    assert abs(agg["grok_rate"] - 0.6) < 1e-9
    assert abs(agg["t_gen_mean"] - 5000.0) < 1e-9  # censored: only the 3 grokked seeds


# --------------------------------------------------------------------------
# decide() verdict ladder
# --------------------------------------------------------------------------
def _config():
    return GrokConfig(seeds=(0, 1, 2, 3, 4), eval_every=200, wds=(1.0, 0.0))


def test_verdict_wd_driven_when_decay_groks_and_ablation_does_not():
    cfg = _config()
    on = [_result(grokked=True, t_gen=5000, val_at_mem=0.02) for _ in range(5)]
    off = [_result(grokked=False, final_val=0.05) for _ in range(5)]
    out = decide(cfg, {1.0: on, 0.0: off})
    assert out["status"] == "pass"
    assert out["verdict"] == "grokking_reproduced_wd_driven"


def test_verdict_wd_accelerates_when_both_grok_but_decay_sooner():
    cfg = _config()
    on = [_result(grokked=True, t_gen=5000 + 50 * i, val_at_mem=0.02) for i in range(5)]
    off = [_result(grokked=True, t_gen=20000 + 50 * i, val_at_mem=0.02) for i in range(5)]
    out = decide(cfg, {1.0: on, 0.0: off})
    assert out["verdict"] == "grokking_reproduced_wd_accelerates"


def test_verdict_not_separable_when_both_grok_at_similar_step():
    cfg = _config()
    on = [_result(grokked=True, t_gen=5000 + 400 * i, val_at_mem=0.02) for i in range(5)]
    off = [_result(grokked=True, t_gen=5200 + 400 * i, val_at_mem=0.02) for i in range(5)]
    out = decide(cfg, {1.0: on, 0.0: off})
    assert out["verdict"] == "grokking_reproduced_wd_not_separable"


def test_verdict_memorized_no_grok_when_decay_arm_rarely_groks():
    cfg = _config()
    on = [_result(grokked=False) for _ in range(5)]
    off = [_result(grokked=False) for _ in range(5)]
    out = decide(cfg, {1.0: on, 0.0: off})
    assert out["status"] == "pass"  # validly measured, just no grok
    assert out["verdict"] == "memorized_no_grok_within_budget"


def test_grok_without_real_delay_is_not_counted_as_reproduced():
    # train and val rose together (val already high at memorization) -> not grokking
    cfg = _config()
    on = [_result(grokked=True, t_mem=4800, t_gen=5000, val_at_mem=0.85) for _ in range(5)]
    off = [_result(grokked=True, t_mem=4800, t_gen=5000, val_at_mem=0.85) for _ in range(5)]
    out = decide(cfg, {1.0: on, 0.0: off})
    assert out["gates"]["delay_real"] is False
    assert out["verdict"] == "memorized_no_grok_within_budget"


def test_status_review_when_decay_arm_cannot_even_memorize():
    cfg = _config()
    on = [_result(grokked=False, memorized=False, final_train=0.2) for _ in range(5)]
    off = [_result(grokked=False, memorized=False, final_train=0.2) for _ in range(5)]
    out = decide(cfg, {1.0: on, 0.0: off})
    assert out["status"] == "review"
    assert out["verdict"] == "no_memorization_training_broken"


def test_status_review_when_grid_incomplete():
    cfg = _config()  # expects 5 seeds
    on = [_result(grokked=True) for _ in range(3)]  # only 3 ran
    off = [_result(grokked=False) for _ in range(3)]
    out = decide(cfg, {1.0: on, 0.0: off})
    assert out["gates"]["g2_grid_complete"] is False
    assert out["status"] == "review"


# --------------------------------------------------------------------------
# tiny end-to-end smoke (CPU): runs, is deterministic, memorizes a small set
# --------------------------------------------------------------------------
def _smoke_config():
    return GrokConfig(
        p=5, train_frac=0.4, n_layer=1, n_head=4, n_embd=16,
        max_steps=400, eval_every=50, seeds=(0, 1), wds=(1.0, 0.0),
    )


def test_smoke_report_shape_and_keys():
    report = run_grok(config=_smoke_config(), device=torch.device("cpu"), generated_at="fixed")
    assert report["status"] in {"pass", "review"}
    assert report["summary"]["p"] == 5
    assert report["summary"]["g0_task_correct"] is True
    assert len(report["rows"]) == 2 * 2  # 2 seeds x 2 arms
    for key in ("seed", "weight_decay", "grokked", "t_mem", "final_train_acc"):
        assert key in report["rows"][0]
    assert report["csv_fieldnames"][0] == "seed"


def test_smoke_is_deterministic():
    a = run_grok(config=_smoke_config(), device=torch.device("cpu"), generated_at="x")
    b = run_grok(config=_smoke_config(), device=torch.device("cpu"), generated_at="x")
    assert a["rows"] == b["rows"]


def test_smoke_memorizes_small_train_set():
    report = run_grok(config=_smoke_config(), device=torch.device("cpu"), generated_at="x")
    wd_on_rows = [r for r in report["rows"] if r["weight_decay"] == 1.0]
    # a 1-layer model trivially fits ~10 training examples within the budget
    assert all(r["final_train_acc"] >= 0.99 for r in wd_on_rows)
