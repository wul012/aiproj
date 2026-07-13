"""v1279 gate tests: t_gen-from-curve censoring, sign-test counting, mediation
share math, every decide() branch on synthetic caches, config validation,
injected-trainer orchestration, byte-stable contract, figure smoke."""
from __future__ import annotations

import json
import math

import torch

from minigpt.grok_speed_v1279 import (
    SpeedConfig,
    build_report,
    decide,
    plot_result,
    run_phase_a,
    scaled_init,
    summarize,
    t_gen_at,
    total_norm_of,
)

CFG = SpeedConfig()


def _curve(t_cross: int | None, max_steps: int = 40000) -> list[tuple[int, float]]:
    """A val-accuracy curve crossing 0.95 at t_cross (None = never)."""
    points = []
    for step in range(100, max_steps + 1, 4000):
        val = 0.97 if (t_cross is not None and step >= t_cross) else 0.05
        points.append((step, val))
    return points


def _cell(arm, width, seed, alpha, t_cross, heldout=0.95):
    return {
        "arm": arm, "width": width, "seed": seed, "alpha": alpha,
        "n0": 10.0 * alpha, "n_final": 5.0,
        "t_mem": 100, "t_gen": t_cross, "steps_run": 40000,
        "final_train_acc": 1.0, "final_val_acc": heldout, "heldout_acc": heldout,
        "curve": _curve(t_cross),
    }


def _cache(wide_t=16100, narrow_t=4100, w16_t=4100, w64_t=8100,
           alpha_half_t=8100, alpha_two_t=None, star_t=4100, sym_t=12100):
    """A full 24-cell synthetic cache; defaults = clean norm-clock world."""
    cells = []
    grid_t = {16: w16_t, 32: narrow_t, 64: w64_t, 128: wide_t}
    for width in CFG.widths:
        for seed in CFG.seeds:
            cells.append(_cell("grid", width, seed, 1.0, grid_t[width]))
    for alpha, t in ((0.5, alpha_half_t), (2.0, alpha_two_t)):
        for seed in CFG.seeds:
            cells.append(_cell("alpha_wide", 128, seed, alpha, t))
    for seed in CFG.seeds:
        cells.append(_cell("alpha_star", 128, seed, 0.467, star_t))
    for seed in CFG.seeds:
        cells.append(_cell("alpha_narrow", 32, seed, 2.0, sym_t))
    return {"schema": "grok_speed_v1279.v1", "generated_at": "t",
            "config": {}, "cells": cells}


# ------------------------------------------------------------------ units ----
def test_t_gen_at_crossing_and_censoring():
    curve = _curve(8100)
    assert t_gen_at(curve, 0.90) == 8100
    assert t_gen_at(_curve(None), 0.90) is None
    assert t_gen_at([(100, 0.96)], 0.95) == 100


def test_scaled_init_scales_total_norm_linearly():
    base = total_norm_of(scaled_init(16, 1337, 1.0, CFG))
    doubled = total_norm_of(scaled_init(16, 1337, 2.0, CFG))
    assert math.isclose(doubled, 2 * base, rel_tol=1e-5)


def test_config_validation():
    for bad in (
        SpeedConfig(widths=(30, 32, 64, 128)),
        SpeedConfig(wide=256),
        SpeedConfig(seeds=tuple(range(9))),
        SpeedConfig(tgen_bars=(0.85, 0.95)),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------- verdicts ----
def test_decide_norm_clock_full_mediation():
    info = decide(_cache())
    # matched-norm cells at the narrow baseline -> share = 1.0
    assert info["verdict"] == "narrow_speedup_is_norm_clock"
    assert info["g0_substrate"] and info["g1_complete"] and info["g2_bar_stable"]
    assert info["main"]["sign"]["state"] == "pass"
    assert math.isclose(info["main"]["mediation"]["share"], 1.0)


def test_decide_partial_and_rejected_shares():
    # matched cells only 35% of the way toward narrow -> partial
    partial = decide(_cache(star_t=12100))  # gap 12000, reduced 8000 -> share 1/3
    assert partial["verdict"] == "norm_clock_partial"
    none = decide(_cache(star_t=16100))     # matched == wide baseline -> share 0
    assert none["verdict"] == "norm_clock_rejected"


def test_decide_alpha_sign_failure_rejects():
    # alpha has no effect: all d=128 alphas grok at the same time
    info = decide(_cache(alpha_half_t=16100, alpha_two_t=16100))
    assert info["main"]["sign"]["state"] == "fail"
    assert info["verdict"] == "norm_clock_rejected"


def test_decide_phenomenon_not_robust_and_review_paths():
    flat = decide(_cache(wide_t=6100, w64_t=5100))  # ratio 6100/4100 < 2
    assert flat["verdict"] == "phenomenon_not_robust"
    inverted = decide(_cache(w64_t=20100))  # ratio >= 2 but middle inversion
    assert inverted["verdict"] == "review"
    incomplete = _cache()
    incomplete["cells"] = incomplete["cells"][:-1]
    assert decide(incomplete)["reason"] == "grid_incomplete"
    broken = _cache()
    for cell in broken["cells"]:
        if cell["arm"] == "grid" and cell["width"] == 64:
            cell["heldout_acc"] = 0.2
            cell["t_gen"] = None
    assert decide(broken)["reason"] == "substrate_unsound"


def test_censored_alpha_two_counts_toward_direction():
    info = decide(_cache(alpha_two_t=None))  # censored = +inf > t(alpha=1)
    assert info["main"]["sign"]["monotone_pairs"] == 6
    assert info["verdict"] == "narrow_speedup_is_norm_clock"


# ------------------------------------------------------- orchestration/etc ----
def test_run_phase_a_with_injected_trainer_and_contract():
    calls = []

    def fake_trainer(cfg, width, seed, alpha, device):
        calls.append((width, seed, round(alpha, 3)))
        t = {16: 4100, 32: 4100, 64: 8100, 128: 16100}[width]
        if width == 128 and alpha < 1.0:
            t = 4100
        if width == 128 and alpha > 1.0:
            t = None
        return _cell("placeholder", width, seed, alpha, t)

    cache = run_phase_a(CFG, torch.device("cpu"), trainer=fake_trainer)
    assert len(cache["cells"]) == CFG.cell_count() == 24
    star_alphas = [a for w, s, a in calls if a not in (1.0, 0.5, 2.0)]
    assert len(star_alphas) == 3 and all(0.4 < a < 0.55 for a in star_alphas)
    first = json.dumps(decide(cache), sort_keys=True)
    second = json.dumps(decide(cache), sort_keys=True)
    assert first == second
    report = build_report(cache, decide(cache))
    assert any(line.startswith("decision=") for line in summarize(report))


def test_plot_result_writes_figure(tmp_path):
    cache = _cache(alpha_two_t=None)
    out = tmp_path / "fig" / "grok-speed-v1279.png"
    plot_result(cache, decide(cache), out)
    assert out.exists() and out.stat().st_size > 10_000
