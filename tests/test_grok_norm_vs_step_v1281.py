"""v1281 gate tests: config validation, G0 on synthetic references, every
ladder branch (parity / small-norm / large-norm / mixed / broken), orchestration
with injected trainer + preloaded probe slot, byte-stable contract, figure smoke."""
from __future__ import annotations

import json
import math

import torch

from minigpt.grok_norm_vs_step_v1281 import (
    StepClockConfig,
    build_report,
    decide,
    plot_result,
    run_phase_a,
    summarize,
)

CFG = StepClockConfig()


def _curve3(t_mem, t_gen, max_steps=60000):
    rows = []
    for step in range(100, max_steps + 1, 100):
        train = 1.0 if (t_mem is not None and step >= t_mem) else 0.2
        val = 0.97 if (t_gen is not None and step >= t_gen) else 0.05
        rows.append((step, train, val))
    return rows


def _cell(arm, alpha, lr, seed, t_mem, t_gen, heldout=0.95):
    return {"arm": arm, "alpha": alpha, "lr": lr, "seed": seed, "n0": 22.0,
            "t_mem": t_mem, "t_gen": t_gen, "steps_run": 60000,
            "final_train_acc": 1.0 if t_mem else 0.3,
            "final_val_acc": heldout, "heldout_acc": heldout,
            "curve": _curve3(t_mem, t_gen)}


def _ref80(medians=((3800, 4000), (1300, 2300))):
    cells = []
    for lr, tgens in zip(CFG.pair_ref_lrs, medians):
        for seed, t in zip((1337, 1338), tgens):
            cells.append(_cell("rescue", 0.5, lr, seed, 300, t, 0.98))
    return {"schema": "grok_init_rescue_v1280.v1", "cells": cells}


def _ref79(base_tgens=(11400, 12700, 10500)):
    cells = []
    for seed, t in zip((1337, 1338, 1339), base_tgens):
        curve = [(step, 0.97 if step >= t else 0.05)
                 for step in range(100, 100001, 100)]
        cells.append({"arm": "grid", "width": 128, "alpha": 1.0, "seed": seed,
                      "t_mem": 300, "t_gen": t, "heldout_acc": 0.96,
                      "curve": curve})
    return {"schema": "grok_speed_v1279.v1", "cells": cells}


def _cache(v4=(4100, 4100, 3900), v8=(1900, 1700, 1800), dose_t=6100,
           sym_t=8100, heldout=0.95):
    """Defaults: alpha=1 at matched step groks at pair-parity speeds."""
    cells = []
    for lr, tgens in zip(CFG.verdict_lrs, (v4, v8)):
        for seed, t in zip(CFG.verdict_seeds, tgens):
            cells.append(_cell("verdict", 1.0, lr, seed,
                               300 if t != "broken" else None,
                               None if t in (None, "broken") else t,
                               heldout if t not in (None, "broken") else 0.2))
    for seed in CFG.side_seeds:
        cells.append(_cell("dose", 1.0, CFG.dose_lr, seed, 300, dose_t))
    for seed in CFG.side_seeds:
        cells.append(_cell("symmetry", CFG.sym_alpha, CFG.sym_lr, seed, 300, sym_t))
    return {"schema": "grok_norm_vs_step_v1281.v1", "generated_at": "t",
            "config": {}, "cells": cells}


# ------------------------------------------------------------------ units ----
def test_config_validation():
    for bad in (
        StepClockConfig(verdict_lrs=(4e-3,)),
        StepClockConfig(pair_ref_lrs=(1e-3, 4e-3)),
        StepClockConfig(sym_lr=4e-3),
        StepClockConfig(tgen_bars=(0.85, 0.95)),
        StepClockConfig(parity_band=(1.5, 2.0)),
        StepClockConfig(max_runs=9),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------- verdicts ----
def test_decide_parity_means_step_sets_the_clock():
    info = decide(_cache(), _ref80(), _ref79())
    assert info["verdict"] == "relative_step_sets_the_clock"
    assert info["g0_references"] and info["g1_complete"] and info["g2_bar_stable"]
    assert info["pairs"]["0.004"]["state"] == "ok"
    assert math.isclose(info["pairs"]["0.004"]["rho"], round(4100 / 3900, 4))


def test_decide_small_and_large_norm_branches():
    slow = decide(_cache(v4=(11900, 12100, 11400), v8=(9900, 10100, 9500)),
                  _ref80(), _ref79())
    assert slow["verdict"] == "small_norm_speeds_grokking_beyond_lr"
    stuck = decide(_cache(v4=(None, None, None), v8=(None, None, None)),
                   _ref80(), _ref79())
    assert stuck["verdict"] == "small_norm_speeds_grokking_beyond_lr"
    fast = decide(_cache(v4=(1100, 1300, 1200), v8=(700, 800, 600)),
                  _ref80(), _ref79())
    assert fast["verdict"] == "large_norm_speeds_grokking_beyond_lr"


def test_decide_mixed_and_broken_route_to_review():
    mixed = decide(_cache(v4=(4100, 4100, 3900), v8=(9900, 10100, 9500)),
                   _ref80(), _ref79())
    assert mixed["verdict"] == "review" and mixed["reason"] == "mixed_pairs"
    broken = decide(_cache(v8=("broken", 1700, 1800)), _ref80(), _ref79())
    assert broken["verdict"] == "review" and broken["reason"] == "broken_cells"
    assert broken["pairs"]["0.008"]["state"] == "broken"


def test_decide_gates():
    bad80 = decide(_cache(), _ref80(medians=((3800, 4200), (1300, 2300))),
                   _ref79())
    assert bad80["reason"] == "reference_cache_invalid"
    bad79 = decide(_cache(), _ref80(), _ref79(base_tgens=(9000, 9400, 9900)))
    assert bad79["reason"] == "reference_cache_invalid"
    incomplete = _cache()
    incomplete["cells"] = incomplete["cells"][:-1]
    assert decide(incomplete, _ref80(), _ref79())["reason"] == "grid_incomplete"


# ------------------------------------------------------- orchestration/etc ----
def test_run_phase_a_with_injected_trainer_and_preloaded_probe():
    trained = []

    def trainer(cfg, alpha, lr, seed, device):
        trained.append((alpha, lr, seed))
        t_gen = 1900 if lr == 8e-3 else 4100  # parity with both pair references
        return _cell("placeholder", alpha, lr, seed, 300, t_gen)

    probe = _cell("ignored", 1.0, 4e-3, 1337, 300, 4300)
    cache = run_phase_a(CFG, torch.device("cpu"), trainer=trainer,
                        preloaded=(probe,))
    assert (1.0, 4e-3, 1337) not in trained
    assert len(cache["cells"]) == CFG.planned_runs() == 10
    slot = [c for c in cache["cells"]
            if c["arm"] == "verdict" and c["lr"] == 4e-3 and c["seed"] == 1337]
    assert len(slot) == 1 and slot[0]["t_gen"] == 4300
    info = decide(cache, _ref80(), _ref79())
    assert info["verdict"] == "relative_step_sets_the_clock"
    assert json.dumps(info, sort_keys=True) == \
        json.dumps(decide(cache, _ref80(), _ref79()), sort_keys=True)
    report = build_report(cache, _ref80(), _ref79(), info)
    assert any(line.startswith("decision=") for line in summarize(report))


def test_plot_result_writes_figure(tmp_path):
    cache = _cache(v4=(None, None, None))
    out = tmp_path / "fig" / "grok-norm-vs-step-v1281.png"
    plot_result(cache, _ref80(), _ref79(), decide(cache, _ref80(), _ref79()), out)
    assert out.exists() and out.stat().st_size > 10_000
