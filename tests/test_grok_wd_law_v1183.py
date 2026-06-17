"""Tests for v1183 grokking weight-decay dose-response.

Fast and CPU-only: the decide_wd_law verdict ladder on synthetic per-arm metrics
(monotone acceleration, non-monotone, threshold-without-trend, insufficient range,
broken training, incomplete grid) plus a tiny end-to-end smoke that reuses the
v1179 training primitive.
"""

from __future__ import annotations

import torch

from minigpt.grok_wd_law_v1183 import WdLawConfig, decide_wd_law, run_wd_law


def _arm(t_gens=None, *, memorized=True, n=5, val_at_mem=0.15, final_val=0.96):
    """Build a list of per-seed arm results. ``t_gens`` is a list with one entry
    per seed: a number for a grokked seed, ``None`` for a non-grokked seed."""
    if t_gens is None:
        t_gens = [None] * n
    out = []
    for tg in t_gens:
        grokked = tg is not None
        out.append(
            {
                "weight_decay": 0.0,
                "memorized": memorized,
                "grokked": grokked,
                "t_mem": 200 if memorized else None,
                "t_gen": tg,
                "grok_gap": (tg - 200) if grokked else None,
                "val_at_mem": val_at_mem if grokked else None,
                "final_train_acc": 1.0 if memorized else 0.2,
                "final_val_acc": final_val if grokked else 0.16,
                "steps_run": 0,
                "curve": [],
            }
        )
    return out


def _config():
    return WdLawConfig(seeds=(0, 1, 2, 3, 4), wds=(0.0, 0.1, 0.3, 1.0, 3.0), eval_every=200)


def test_verdict_monotone_acceleration():
    cfg = _config()
    rbw = {
        0.0: _arm(),
        0.1: _arm(),
        0.3: _arm([29000, 30000, 31000, 30000, 30000]),
        1.0: _arm([14000, 15000, 16000, 15000, 15000]),
        3.0: _arm([7500, 8000, 8500, 8000, 8000]),
    }
    out = decide_wd_law(cfg, rbw, g0_task_correct=True)
    assert out["status"] == "pass"
    assert out["verdict"] == "wd_dose_response_monotone_acceleration"
    assert out["grok_wds"] == [0.3, 1.0, 3.0]
    assert out["threshold_wd"] == 0.3
    assert out["censored_below_threshold"] is True


def test_verdict_interior_optimum_when_strongest_wd_does_not_grok():
    # too-little (<=0.1) AND too-much (3.0) decay fail to grok within budget,
    # though 3.0 still memorizes -> non-monotone with an interior optimum.
    cfg = _config()
    rbw = {
        0.0: _arm(),
        0.1: _arm(),
        0.3: _arm([29000, 30000, 31000, 30000, 30000]),
        1.0: _arm([14000, 15000, 16000, 15000, 15000]),
        3.0: _arm(memorized=True),  # memorizes 5/5 but groks 0/5
    }
    out = decide_wd_law(cfg, rbw, g0_task_correct=True)
    assert out["status"] == "pass"
    assert out["interior_optimum"] is True
    assert out["high_end_grok_censored"] is True
    assert out["too_much_wd_breaks_memorization"] is False
    assert out["best_wd"] == 1.0
    assert out["verdict"] == "wd_dose_response_interior_optimum"


def test_verdict_nonmonotone_but_accelerates():
    cfg = _config()
    rbw = {
        0.0: _arm(),
        0.1: _arm(),
        0.3: _arm([19000, 20000, 21000, 20000, 20000]),
        1.0: _arm([24000, 25000, 26000, 25000, 25000]),  # bump up -> not monotone
        3.0: _arm([7500, 8000, 8500, 8000, 8000]),
    }
    out = decide_wd_law(cfg, rbw, g0_task_correct=True)
    assert out["monotone"] is False
    assert out["accelerates_significant"] is True
    assert out["verdict"] == "wd_accelerates_grok_nonmonotone"


def test_verdict_threshold_without_trend():
    cfg = _config()
    rbw = {
        0.0: _arm(),
        0.1: _arm(),
        0.3: _arm([15000, 16000, 14000, 15000, 15000]),
        1.0: _arm([14000, 15000, 13000, 14000, 14000]),
        3.0: _arm([14500, 15500, 13500, 14500, 14500]),
    }
    out = decide_wd_law(cfg, rbw, g0_task_correct=True)
    assert out["accelerates_significant"] is False
    assert out["verdict"] == "wd_threshold_without_clear_step_trend"


def test_verdict_insufficient_grok_range():
    cfg = _config()
    rbw = {
        0.0: _arm(),
        0.1: _arm(),
        0.3: _arm(),
        1.0: _arm([14000, 15000, 16000, 15000, 15000]),  # only this one groks
        3.0: _arm(),
    }
    out = decide_wd_law(cfg, rbw, g0_task_correct=True)
    assert out["status"] == "pass"
    assert out["verdict"] == "insufficient_grok_range_to_characterize"


def test_verdict_no_memorization_when_reference_arm_cannot_fit():
    cfg = _config()
    rbw = {wd: _arm(memorized=False) for wd in cfg.wds}
    out = decide_wd_law(cfg, rbw, g0_task_correct=True)
    assert out["status"] == "review"
    assert out["verdict"] == "no_memorization_training_broken"


def test_status_review_when_grid_incomplete():
    cfg = _config()
    rbw = {
        0.0: _arm(),
        0.1: _arm(),
        0.3: _arm([30000, 30000, 30000]),  # only 3 seeds ran
        1.0: _arm([15000, 15000, 15000, 15000, 15000]),
        3.0: _arm([8000, 8000, 8000, 8000, 8000]),
    }
    out = decide_wd_law(cfg, rbw, g0_task_correct=True)
    assert out["gates"]["g2_grid_complete"] is False
    assert out["status"] == "review"


def test_too_much_wd_breaks_memorization_flag():
    cfg = _config()
    rbw = {
        0.0: _arm(),
        0.1: _arm([30000, 31000, 29000, 30000, 30000]),
        0.3: _arm([20000, 21000, 19000, 20000, 20000]),
        1.0: _arm([14000, 15000, 13000, 14000, 14000]),
        3.0: _arm(memorized=False),  # strongest wd fails to even memorize
    }
    out = decide_wd_law(cfg, rbw, g0_task_correct=True)
    assert out["too_much_wd_breaks_memorization"] is True


# --------------------------------------------------------------------------
# tiny end-to-end smoke (CPU): reuses the v1179 training primitive
# --------------------------------------------------------------------------
def _smoke_config():
    return WdLawConfig(
        p=5, train_frac=0.4, n_layer=1, n_head=4, n_embd=16,
        max_steps=300, eval_every=100, seeds=(0, 1), wds=(0.0, 1.0),
    )


def test_smoke_report_shape():
    report = run_wd_law(config=_smoke_config(), device=torch.device("cpu"), generated_at="fixed")
    assert report["status"] in {"pass", "review"}
    assert report["summary"]["p"] == 5
    assert len(report["rows"]) == 2  # one dose-response row per weight_decay
    assert len(report["seed_rows"]) == 2 * 2  # 2 seeds x 2 wds
    assert report["rows"][0]["weight_decay"] == 0.0
    assert "grok_rate" in report["rows"][0]


def test_smoke_is_deterministic():
    a = run_wd_law(config=_smoke_config(), device=torch.device("cpu"), generated_at="x")
    b = run_wd_law(config=_smoke_config(), device=torch.device("cpu"), generated_at="x")
    assert a["rows"] == b["rows"] and a["seed_rows"] == b["seed_rows"]
