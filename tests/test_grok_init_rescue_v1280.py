"""v1280 gate tests: cell classification (incl. heldout gate and broken class),
t_mem-from-train-curve, config validation, G0 reference integrity, every decide()
branch on synthetic caches, the deterministic confirm rule with an injected
trainer, byte-stable contract, figure smoke."""
from __future__ import annotations

import json

import torch

from minigpt.grok_init_rescue_v1280 import (
    RescueConfig,
    build_report,
    classify,
    decide,
    plot_result,
    run_phase_a,
    summarize,
    t_mem_at,
)

CFG = RescueConfig()


def _curve3(t_mem: int | None, t_gen: int | None,
            max_steps: int = 60000) -> list[tuple[int, float, float]]:
    rows = []
    for step in range(100, max_steps + 1, 4000):
        train = 1.0 if (t_mem is not None and step >= t_mem) else 0.2
        val = 0.97 if (t_gen is not None and step >= t_gen) else 0.05
        rows.append((step, train, val))
    return rows


def _cell(arm, alpha, lr, seed, t_mem, t_gen, heldout=0.95):
    return {"arm": arm, "alpha": alpha, "lr": lr, "seed": seed, "n0": 11.0,
            "t_mem": t_mem, "t_gen": t_gen, "steps_run": 60000,
            "final_train_acc": 1.0 if t_mem else 0.3,
            "final_val_acc": heldout, "heldout_acc": heldout,
            "curve": _curve3(t_mem, t_gen)}


def _ref_cell(arm, width, alpha, seed, t_mem, t_gen, heldout=0.96):
    # the real v1279 cache evals every 100 steps; G0 pins the exact median 11400,
    # so the synthetic grid must contain the crossing steps exactly
    curve = [(step, 0.97 if (t_gen is not None and step >= t_gen) else 0.05)
             for step in range(100, 100001, 100)]
    return {"arm": arm, "width": width, "seed": seed, "alpha": alpha, "n0": 22.0,
            "t_mem": t_mem, "t_gen": t_gen, "heldout_acc": heldout, "curve": curve}


def _reference(base_tgens=(11400, 12700, 10500), dead_ok=True):
    cells = []
    for seed, t in zip((1337, 1338, 1339), base_tgens):
        cells.append(_ref_cell("grid", 128, 1.0, seed, 300, t))
    for arm, alpha in (("alpha_wide", 0.5), ("alpha_star", 0.493)):
        for seed in (1337, 1338, 1339):
            cells.append(_ref_cell(arm, 128, alpha, seed,
                                   300 if dead_ok else None, None, heldout=0.2))
    for seed in (1337, 1338, 1339):  # alpha=2 cells must be excluded by the filter
        cells.append(_ref_cell("alpha_wide", 128, 2.0, seed, 300, 20000))
    return {"schema": "grok_speed_v1279.v1", "cells": cells}


def _cache(rescue_tgen=None, confirm=(), dose_tgens=(None, None, 24000),
           rescue_heldout=0.2):
    """Default: nothing rescued, dose groks only at alpha=0.85."""
    cells = []
    for lr in CFG.rescue_lrs:
        for seed in CFG.seeds:
            spec = rescue_tgen(lr, seed) if callable(rescue_tgen) else None
            heldout = 0.95 if spec else rescue_heldout
            cells.append(_cell("rescue", 0.5, lr, seed, 300, spec, heldout))
    for lr, t in confirm:
        cells.append(_cell("rescue_confirm", 0.5, lr, 1339, 300, t,
                           0.95 if t else 0.2))
    for alpha, t in zip(CFG.dose_alphas, dose_tgens):
        for seed in CFG.seeds:
            cells.append(_cell("dose", alpha, CFG.base_lr, seed, 300, t,
                               0.95 if t else 0.2))
    return {"schema": "grok_init_rescue_v1280.v1", "generated_at": "t",
            "config": {}, "cells": cells}


# ------------------------------------------------------------------ units ----
def test_t_mem_and_classification():
    assert t_mem_at(_curve3(4100, None), 0.99) == 4100
    assert t_mem_at(_curve3(None, None), 0.99) is None
    assert classify(_cell("rescue", 0.5, 1e-3, 1, 300, 8100), 0.90, CFG) == "grokked"
    stuck = _cell("rescue", 0.5, 1e-3, 1, 300, None, heldout=0.2)
    assert classify(stuck, 0.90, CFG) == "stuck_memorized"
    broken = _cell("rescue", 0.5, 4e-3, 1, None, None, heldout=0.05)
    assert classify(broken, 0.90, CFG) == "broken"
    # val crossing without heldout does NOT count as grokked
    lucky = _cell("rescue", 0.5, 1e-3, 1, 300, 8100, heldout=0.5)
    assert classify(lucky, 0.90, CFG) == "stuck_memorized"
    # reference cells (2-column curve) classify through their t_mem field
    ref_dead = _ref_cell("alpha_wide", 128, 0.5, 1, 300, None, heldout=0.2)
    assert classify(ref_dead, 0.90, CFG) == "stuck_memorized"


def test_config_validation():
    for bad in (
        RescueConfig(rescue_lrs=(1e-3, 2e-3)),
        RescueConfig(dose_alphas=(0.4, 0.7)),
        RescueConfig(confirm_seed=1337),
        RescueConfig(tgen_bars=(0.85, 0.95)),
        RescueConfig(max_runs=15),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------- verdicts ----
def test_decide_stuck_robust_to_lr():
    info = decide(_cache(), _reference())
    assert info["verdict"] == "stuck_memorized_robust_to_lr"
    assert info["g0_reference"] and info["g1_complete"] and info["g2_bar_stable"]
    assert info["rescued_lrs"] == []
    # 0.6/0.7 stuck, 0.85 grokked, unanimous seeds -> single transition = cliff
    assert info["dose_shape"] == "cliff"


def test_dose_cliff_and_graded():
    cliff = decide(_cache(dose_tgens=(None, None, 24000)), _reference())
    assert cliff["dose_shape"] == "cliff"
    graded = decide(_cache(dose_tgens=(None, 24000, None)), _reference())
    assert graded["dose_shape"] == "graded"


def test_decide_rescued_faster_and_slower():
    fast = decide(_cache(rescue_tgen=lambda lr, s: 6100 if lr == 5e-4 else None),
                  _reference())
    assert fast["verdict"] == "norm_clock_revived_under_lr_scaling"
    assert fast["rescued_lrs"] == [5e-4]
    slow = decide(_cache(rescue_tgen=lambda lr, s: 30100 if lr == 5e-4 else None),
                  _reference())
    assert slow["verdict"] == "lr_rescues_grokking_without_speedup"


def test_decide_confirm_promotes_single_seed_rescue():
    one_seed = _cache(rescue_tgen=lambda lr, s: 6100 if (lr == 5e-4 and s == 1337)
                      else None,
                      confirm=((5e-4, 6100),))
    info = decide(one_seed, _reference())
    assert info["g1_complete"]
    assert info["verdict"] == "norm_clock_revived_under_lr_scaling"
    failed_confirm = _cache(rescue_tgen=lambda lr, s: 6100 if (lr == 5e-4 and s == 1337)
                            else None,
                            confirm=((5e-4, None),))
    assert decide(failed_confirm, _reference())["verdict"] == \
        "stuck_memorized_robust_to_lr"


def test_decide_gates():
    bad_ref = decide(_cache(), _reference(dead_ok=False))
    assert bad_ref["reason"] == "reference_cache_invalid"
    wrong_median = decide(_cache(), _reference(base_tgens=(9000, 9400, 9900)))
    assert wrong_median["reason"] == "reference_cache_invalid"
    incomplete = _cache()
    incomplete["cells"] = incomplete["cells"][:-1]
    assert decide(incomplete, _reference())["reason"] == "grid_incomplete"
    missing_confirm = _cache(rescue_tgen=lambda lr, s: 6100 if (lr == 5e-4 and s == 1337)
                             else None)  # rule fires but no confirm cell cached
    assert decide(missing_confirm, _reference())["reason"] == "grid_incomplete"


# ------------------------------------------------------- orchestration/etc ----
def test_run_phase_a_confirm_rule_with_injected_trainer():
    def trainer(cfg, alpha, lr, seed, device):
        t_gen = 6100 if (lr == 5e-4 and alpha == 0.5 and seed in (1337, 1339)) \
            else None
        return _cell("placeholder", alpha, lr, seed, 300, t_gen,
                     0.95 if t_gen else 0.2)

    cache = run_phase_a(CFG, torch.device("cpu"), trainer=trainer)
    confirms = [c for c in cache["cells"] if c["arm"] == "rescue_confirm"]
    assert [c["lr"] for c in confirms] == [5e-4]
    assert confirms[0]["seed"] == CFG.confirm_seed
    assert len(cache["cells"]) == CFG.planned_min() + 1
    info = decide(cache, _reference())
    assert info["verdict"] == "norm_clock_revived_under_lr_scaling"
    first = json.dumps(info, sort_keys=True)
    assert first == json.dumps(decide(cache, _reference()), sort_keys=True)
    report = build_report(cache, _reference(), info)
    assert any(line.startswith("decision=") for line in summarize(report))


def test_plot_result_writes_figure(tmp_path):
    cache = _cache()
    out = tmp_path / "fig" / "grok-init-rescue-v1280.png"
    plot_result(cache, _reference(), decide(cache, _reference()), out)
    assert out.exists() and out.stat().st_size > 10_000
