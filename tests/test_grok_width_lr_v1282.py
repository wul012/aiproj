"""v1282 gate tests: config validation, G0 fail paths for both reference caches,
every ladder branch, conditional hole-probe orchestration, preloaded probe slot,
byte-stable contract, figure smoke."""
from __future__ import annotations

import json

import torch

from minigpt.grok_width_lr_v1282 import (
    WidthLrConfig,
    build_report,
    decide,
    plot_result,
    run_phase_a,
    summarize,
)

CFG = WidthLrConfig()


def _curve3(t_mem, t_gen, max_steps=60000):
    rows = []
    for step in range(100, max_steps + 1, 100):
        train = 1.0 if (t_mem is not None and step >= t_mem) else 0.2
        val = 0.97 if (t_gen is not None and step >= t_gen) else 0.05
        rows.append((step, train, val))
    return rows


def _cell(arm, width, lr, seed, t_mem, t_gen, heldout=0.95):
    return {"arm": arm, "width": width, "alpha": 1.0, "lr": lr, "seed": seed,
            "n0": 15.0, "t_mem": t_mem, "t_gen": t_gen, "steps_run": 60000,
            "final_train_acc": 1.0 if t_mem else 0.3,
            "final_val_acc": heldout, "heldout_acc": heldout,
            "curve": _curve3(t_mem, t_gen)}


def _ref81(tgens=(1400, 1800, 1000)):
    cells = [_cell("verdict", 128, 4e-3, seed, 300, t, 0.99)
             for seed, t in zip((1337, 1338, 1339), tgens)]
    return {"schema": "grok_norm_vs_step_v1281.v1", "cells": cells}


def _ref79(w64_tgens=(None, 35000, None)):
    grid = {16: (2800, 2600, 6600), 32: (2600, 3400, 2700),
            64: w64_tgens, 128: (11400, 12700, 10500)}
    cells = []
    for width, tgens in grid.items():
        for seed, t in zip((1337, 1338, 1339), tgens):
            curve = [(step, 0.97 if (t is not None and step >= t) else 0.05)
                     for step in range(100, 100001, 100)]
            cells.append({"arm": "grid", "width": width, "alpha": 1.0,
                          "seed": seed, "t_mem": 300, "t_gen": t,
                          "heldout_acc": 0.96 if t else 0.2, "curve": curve})
    return {"schema": "grok_speed_v1279.v1", "cells": cells}


def _cache(w16=(1200, 1500, 1300), w32=(1100, 1600, 1400),
           w64=(1300, 1700, 1500), probes=()):
    cells = []
    for width, tgens in ((16, w16), (32, w32), (64, w64)):
        for seed, t in zip(CFG.seeds, tgens):
            broken = t == "broken"
            cells.append(_cell("width", width, CFG.lr, seed,
                               None if broken else 300,
                               None if (t is None or broken) else t,
                               0.95 if (t and not broken) else 0.2))
    for seed, t in probes:
        cells.append(_cell("hole_probe", 64, CFG.hole_lr, seed, 300, t,
                           0.95 if t else 0.2))
    return {"schema": "grok_width_lr_v1282.v1", "generated_at": "t",
            "config": {}, "cells": cells}


# ------------------------------------------------------------------ units ----
def test_config_validation():
    for bad in (
        WidthLrConfig(verdict_widths=(16, 30, 64)),
        WidthLrConfig(hole_width=128),
        WidthLrConfig(hole_lr=4e-3),
        WidthLrConfig(tgen_bars=(0.85, 0.95)),
        WidthLrConfig(max_runs=10),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------- verdicts ----
def test_decide_collapse():
    info = decide(_cache(), _ref81(), _ref79())
    assert info["verdict"] == "width_clock_collapses_to_lr"
    assert info["g0_references"] and info["g1_complete"] and info["g2_bar_stable"]
    assert info["width_states"] == {"16": "converged", "32": "converged",
                                    "64": "converged"}
    assert not info["hole_rule_fired"]


def test_decide_narrow_survives_and_hole_survives():
    narrow = decide(_cache(w16=(500, 600, 400), w32=(500, 700, 600)),
                    _ref81(), _ref79())
    assert narrow["verdict"] == "narrow_speedup_survives_lr"
    hole = decide(_cache(w64=(None, None, 40000),
                         probes=((1337, 2000), (1338, 2500))),
                  _ref81(), _ref79())
    assert hole["verdict"] == "mid_width_hole_survives_lr"
    assert hole["hole_rule_fired"] and hole["g1_complete"]


def test_decide_mixed_and_broken_route_to_review():
    mixed = decide(_cache(w16=(400, 500, 300), w64=(None, None, None),
                          probes=((1337, None), (1338, None))),
                   _ref81(), _ref79())
    assert mixed["verdict"] == "review" and mixed["reason"] == "mixed_widths"
    broken = decide(_cache(w16=("broken", 1500, 1300)), _ref81(), _ref79())
    assert broken["verdict"] == "review" and broken["reason"] == "broken_cells"


def test_decide_gates():
    bad81 = decide(_cache(), _ref81(tgens=(1400, 1800, 1600)), _ref79())
    assert bad81["reason"] == "reference_cache_invalid"
    bad79 = decide(_cache(), _ref81(), _ref79(w64_tgens=(30000, 35000, 40000)))
    assert bad79["reason"] == "reference_cache_invalid"
    missing_probe = decide(_cache(w64=(None, None, None)), _ref81(), _ref79())
    assert missing_probe["reason"] == "grid_incomplete"
    extra_probe = decide(_cache(probes=((1337, 2000), (1338, 2500))),
                         _ref81(), _ref79())
    assert extra_probe["reason"] == "grid_incomplete"


# ------------------------------------------------------- orchestration/etc ----
def test_run_phase_a_conditional_probe_and_preloaded_slot():
    def stall_trainer(cfg, alpha, lr, seed, device):
        t = None if (cfg.width == 64 and lr == 4e-3) else 1400
        return _cell("placeholder", cfg.width, lr, seed, 300, t,
                     0.95 if t else 0.2)

    probe = _cell("ignored", 64, 4e-3, 1337, 300, None, 0.2)
    cache = run_phase_a(CFG, torch.device("cpu"), trainer=stall_trainer,
                        preloaded=(probe,))
    probes = [c for c in cache["cells"] if c["arm"] == "hole_probe"]
    assert [c["seed"] for c in probes] == list(CFG.hole_seeds)
    assert len(cache["cells"]) == 11

    def fast_trainer(cfg, alpha, lr, seed, device):
        return _cell("placeholder", cfg.width, lr, seed, 300, 1400)

    cache2 = run_phase_a(CFG, torch.device("cpu"), trainer=fast_trainer)
    assert len(cache2["cells"]) == 9
    info = decide(cache2, _ref81(), _ref79())
    assert info["verdict"] == "width_clock_collapses_to_lr"
    assert json.dumps(info, sort_keys=True) == \
        json.dumps(decide(cache2, _ref81(), _ref79()), sort_keys=True)
    report = build_report(cache2, _ref81(), _ref79(), info)
    assert any(line.startswith("decision=") for line in summarize(report))


def test_plot_result_writes_figure(tmp_path):
    cache = _cache(w64=(None, None, 40000), probes=((1337, 2000), (1338, 2500)))
    out = tmp_path / "fig" / "grok-width-lr-v1282.png"
    plot_result(cache, _ref81(), _ref79(), decide(cache, _ref81(), _ref79()), out)
    assert out.exists() and out.stat().st_size > 10_000
