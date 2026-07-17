"""v1283 gate tests: phase classifier units (incl. failed and both threshold
pairs), config validation, G0 anchor mismatch, every ladder branch,
orchestration + preloaded probe slot, byte-stable contract, figure smoke."""
from __future__ import annotations

import json

import torch

from minigpt.grok_delay_gate_v1283 import (
    DelayGateConfig,
    build_report,
    classify_phase,
    decide,
    max_train_val_gap,
    plot_result,
    run_phase_a,
    summarize,
)

CFG = DelayGateConfig()


def _curve(max_gap: float, t_gen: int = 3000, max_steps: int = 60000):
    """A curve whose max train-val gap is exactly max_gap, val grokking at t_gen."""
    rows = []
    for step in range(100, max_steps + 1, 100):
        train = min(1.0, 0.2 + step / 1000)
        val = 0.97 if step >= t_gen else max(0.02, train - max_gap)
        rows.append((step, train, val))
    return rows


def _cell(arm, width, seed, max_gap, t_gen=3000, heldout=0.95):
    t_mem = next((r[0] for r in _curve(max_gap, t_gen) if r[1] >= 0.99), None)
    return {"arm": arm, "width": width, "alpha": 1.0, "lr": 1e-3, "seed": seed,
            "n0": 9.0, "t_mem": t_mem, "t_gen": t_gen if heldout >= 0.9 else None,
            "steps_run": 60000, "final_train_acc": 1.0,
            "final_val_acc": heldout, "heldout_acc": heldout,
            "curve": _curve(max_gap, t_gen)}


def _cache(w20=0.3, w24=0.3, w28=0.9, anchors=(0.3, 0.9), overrides=()):
    """Default: sharp onset between 24 and 28. overrides = per-cell tweaks."""
    cells = []
    gaps = {20: w20, 24: w24, 28: w28}
    for width in CFG.boundary_widths:
        for seed in CFG.seeds:
            cells.append(_cell("boundary", width, seed, gaps[width]))
    for width, gap in zip(CFG.anchor_widths, anchors):
        for seed in CFG.anchor_seeds:
            cells.append(_cell("anchor", width, seed, gap))
    for (width, seed), tweak in overrides:
        for c in cells:
            if c["width"] == width and c["seed"] == seed:
                c.update(tweak)
    return {"schema": "grok_delay_gate_v1283.v1", "generated_at": "t",
            "config": {}, "cells": cells}


# ------------------------------------------------------------------ units ----
def test_phase_classifier():
    coupled = _cell("boundary", 20, 1, 0.3)
    delayed = _cell("boundary", 28, 1, 0.9)
    middle = _cell("boundary", 24, 1, 0.6)
    failed = _cell("boundary", 24, 1, 0.3, heldout=0.5)
    pair = CFG.threshold_pairs[0]
    assert classify_phase(coupled, pair, CFG) == "coupled"
    assert classify_phase(delayed, pair, CFG) == "delayed"
    assert classify_phase(middle, pair, CFG) == "intermediate"
    assert classify_phase(failed, pair, CFG) == "failed"
    # the wider pair reclassifies the middle cell as coupled/delayed edge cases
    assert classify_phase(middle, (0.4, 0.8), CFG) == "intermediate"
    assert abs(max_train_val_gap(coupled) - 0.3) < 1e-9


def test_config_validation():
    for bad in (
        DelayGateConfig(boundary_widths=(20, 25, 28)),
        DelayGateConfig(boundary_widths=(28, 24, 20)),
        DelayGateConfig(anchor_widths=(24, 32)),
        DelayGateConfig(threshold_pairs=((0.7, 0.5),)),
        DelayGateConfig(max_runs=12),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------- verdicts ----
def test_decide_sharp_and_graded():
    sharp = decide(_cache())
    assert sharp["verdict"] == "delayed_phase_onset_is_sharp"
    assert sharp["g0_anchors"] and sharp["g1_complete"]
    assert sharp["g2_threshold_stable"]
    assert sharp["width_classes"] == {"20": "coupled", "24": "coupled",
                                      "28": "delayed"}
    graded = decide(_cache(w24=0.6))
    assert graded["verdict"] == "delayed_phase_onset_is_graded"


def test_decide_review_paths():
    nonmono = decide(_cache(w20=0.9, w24=0.3))
    assert nonmono["verdict"] == "review" and nonmono["reason"] == "mixed_widths"
    mixed = decide(_cache(overrides=(((24, 1338), {"curve": _curve(0.9)}),)))
    assert mixed["reason"] == "mixed_widths"
    unsound = decide(_cache(overrides=(
        ((24, 1337), {"heldout_acc": 0.5}), ((24, 1338), {"heldout_acc": 0.5}))))
    assert unsound["reason"] == "substrate_unsound"
    one_failed_ok = decide(_cache(overrides=(((24, 1337), {"heldout_acc": 0.5}),)))
    assert one_failed_ok["verdict"] == "delayed_phase_onset_is_sharp"


def test_decide_gates_and_threshold_stability():
    bad_anchor = decide(_cache(anchors=(0.9, 0.9)))
    assert bad_anchor["reason"] == "anchor_mismatch"
    incomplete = _cache()
    incomplete["cells"] = incomplete["cells"][1:]  # drop a boundary cell
    assert decide(incomplete)["reason"] == "grid_incomplete"
    # gap 0.45 is coupled at (0.5,0.7) but intermediate at (0.4,0.8) -> flip
    flip = decide(_cache(w24=0.45))
    assert flip["reason"] == "threshold_instability"


# ------------------------------------------------------- orchestration/etc ----
def test_run_phase_a_with_injected_trainer_and_preloaded_probe():
    trained = []

    def trainer(cfg, alpha, lr, seed, device):
        trained.append((cfg.width, seed))
        gap = 0.3 if cfg.width <= 24 else 0.9
        return _cell("placeholder", cfg.width, seed, gap)

    probe = _cell("ignored", 24, 1337, 0.3)
    cache = run_phase_a(CFG, torch.device("cpu"), trainer=trainer,
                        preloaded=(probe,))
    assert (24, 1337) not in trained
    assert len(cache["cells"]) == 13
    info = decide(cache)
    assert info["verdict"] == "delayed_phase_onset_is_sharp"
    assert json.dumps(info, sort_keys=True) == \
        json.dumps(decide(cache), sort_keys=True)
    report = build_report(cache, info)
    assert any(line.startswith("decision=") for line in summarize(report))


def test_plot_result_writes_figure(tmp_path):
    cache = _cache(w24=0.6)
    out = tmp_path / "fig" / "grok-delay-gate-v1283.png"
    plot_result(cache, decide(cache), out)
    assert out.exists() and out.stat().st_size > 10_000
