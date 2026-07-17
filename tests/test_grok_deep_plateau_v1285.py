"""v1285 gate tests: config validation, all G0 paths incl. reference mismatch,
all four ladder branches + dispersion guard + bar instability, orchestration
with injected snapshots + P2 preload, byte-stable contract, figure smoke."""
from __future__ import annotations

import json

import torch

from minigpt.grok_deep_plateau_v1285 import (
    DeepPlateauConfig,
    build_report,
    decide,
    plot_result,
    run_phase_a,
    summarize,
)

CFG = DeepPlateauConfig()
REFS = {1337: (11400, 0.965989), 1338: (12700, 0.951906),
        1339: (10500, 0.970772)}


def _reference():
    cells = []
    for seed, (t_gen, heldout) in REFS.items():
        curve = [(step, 0.12 if step < t_gen else 0.97)
                 for step in range(100, t_gen + 201, 100)]
        cells.append({"arm": "grid", "width": 128, "alpha": 1.0, "seed": seed,
                      "t_mem": 100, "t_gen": t_gen, "heldout_acc": heldout,
                      "curve": curve})
    return {"schema": "grok_speed_v1279.v1", "cells": cells}


def _curve3(t_gen, steps_run, val_bump=None):
    rows = []
    for step in range(100, steps_run + 1, 100):
        val = 0.12 if step < t_gen else 0.97
        if val_bump and step == val_bump[0]:
            val = val_bump[1]
        rows.append((step, 1.0, val))
    return rows


def _cell(seed, share_fn, t_gen=None, heldout=None, val_bump=None):
    t_gen = t_gen or REFS[seed][0]
    heldout = heldout if heldout is not None else REFS[seed][1]
    steps_run = t_gen + 200
    curve = _curve3(t_gen, steps_run, val_bump)
    by_step = dict((r[0], r) for r in curve)
    snapshots = []
    for k in CFG.ladder:
        if k >= steps_run:
            break
        row = by_step[k]
        snapshots.append({"k": k, "train_acc": row[1], "val_acc": row[2],
                          "share": share_fn(k), "prefix_ok": True})
    return {"width": 128, "seed": seed, "expected_phase": "delayed",
            "steps_run": steps_run, "t_mem": 100, "t_gen": t_gen,
            "heldout_acc": heldout, "curve": curve, "top5": [0, 1, 2, 3, 4],
            "final_share": 0.8, "c0_share": 0.1, "prefix_ok": True,
            "snapshots": snapshots}


def _share_sculpt(k):
    return 0.1 + 0.7 * min(1.0, k / 9000)


def _share_late(k):
    return 0.1  # flat through every snapshot; only the final model is at 0.8


def _share_partial(k):
    return 0.1 + 0.245 * min(1.0, k / 10400)


def _cache(share_fns=None, tweaks=()):
    share_fns = share_fns or {s: _share_partial for s in CFG.seeds}
    cells = [_cell(seed, share_fns[seed]) for seed in CFG.seeds]
    for seed, patch in tweaks:
        for c in cells:
            if c["seed"] == seed:
                c.update(patch)
    return {"schema": "grok_deep_plateau_v1285.v1", "generated_at": "t",
            "config": {}, "cells": cells, "runs": 45, "total_steps": 200000}


# ------------------------------------------------------------------ units ----
def test_config_validation():
    for bad in (
        DeepPlateauConfig(width=130),
        DeepPlateauConfig(ladder=(100, 250)),
        DeepPlateauConfig(pre_bar=0.4),
        DeepPlateauConfig(seeds=(1337, 1338)),
        DeepPlateauConfig(max_runs=40),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------- verdicts ----
def test_decide_three_main_branches():
    sculpt = decide(_cache({s: _share_sculpt for s in CFG.seeds}), _reference())
    assert sculpt["verdict"] == "deep_plateau_sculpts"
    assert sculpt["g0_ok"] and sculpt["g1_complete"] and sculpt["g2_bar_stable"]
    late = decide(_cache({s: _share_late for s in CFG.seeds}), _reference())
    assert late["verdict"] == "construction_is_late_everywhere"
    partial = decide(_cache(), _reference())
    assert partial["verdict"] == "partial_early_construction"
    assert 0.2 < partial["f_median"] < 0.5


def test_decide_dispersion_and_bar_instability():
    mixed = decide(_cache({1337: _share_late, 1338: _share_partial,
                           1339: _share_sculpt}), _reference())
    assert mixed["verdict"] == "review" and mixed["reason"] == "mixed_seeds"
    # a gradual final approach (val 0.27@7000, 0.33@8600, then 0.97) makes
    # t_pre bar-dependent while the share crosses bin boundaries between those
    # snapshots -> the three bars give three different verdicts
    def ramp_share(k):
        return 0.15 if k <= 5600 else (0.35 if k <= 7000 else 0.6)

    cache = _cache({s: ramp_share for s in CFG.seeds})
    for c in cache["cells"]:
        for snap in c["snapshots"]:
            if snap["k"] == 7000:
                snap["val_acc"] = 0.27
            if snap["k"] == 8600:
                snap["val_acc"] = 0.33
            if snap["k"] > 8600:
                snap["val_acc"] = 0.97
    info = decide(cache, _reference())
    assert info["reason"] == "bar_instability"


def test_decide_g0_paths():
    bad_prefix = decide(_cache(tweaks=((1337, {"prefix_ok": False}),)),
                        _reference())
    assert bad_prefix["reason"] == "prefix_nondeterministic"
    bad_ref = decide(_cache(tweaks=((1337, {"t_gen": 11500}),)), _reference())
    assert bad_ref["reason"] == "reference_mismatch"
    bad_heldout = decide(_cache(tweaks=((1337, {"heldout_acc": 0.96}),)),
                         _reference())
    assert bad_heldout["reason"] == "reference_mismatch"
    coupled_curve = [(step, min(1.0, 0.3 + step / 8000),
                      min(0.97, 0.28 + step / 8000))
                     for step in range(100, 11801, 100)]
    swapped = decide(_cache(tweaks=((1337, {"curve": coupled_curve}),)),
                     _reference())
    assert swapped["reason"] == "phase_mismatch"
    incomplete = _cache()
    incomplete["cells"][0]["snapshots"] = incomplete["cells"][0]["snapshots"][:-1]
    assert decide(incomplete, _reference())["reason"] == "grid_incomplete"


# ------------------------------------------------------- orchestration/etc ----
def _fake_snapshot(cfg, width, seed, steps, device):
    t_gen, heldout = REFS[seed]
    steps_run = min(steps, t_gen + 200)
    curve = _curve3(t_gen, steps_run)
    last = curve[-1]
    # partial world: C grows to ~0.345 through the plateau, jumps to 0.8 at grok
    tp = 0.8 if steps_run >= t_gen else _share_partial(steps_run)
    power = [tp / 5] * 5 + [(1 - tp) / 43] * 43
    out = {"steps": steps_run, "train_acc": last[1], "val_acc": last[2],
           "power": power}
    if steps >= cfg.max_steps:
        out |= {"t_mem": 100, "t_gen": t_gen, "heldout_acc": heldout,
                "curve": curve}
    return out


def test_run_phase_a_with_injected_snapshots_and_preload():
    cache = run_phase_a(CFG, torch.device("cpu"), snapshot_fn=_fake_snapshot)
    assert len(cache["cells"]) == 3
    info = decide(cache, _reference())
    assert info["verdict"] == "partial_early_construction"
    assert json.dumps(info, sort_keys=True) == \
        json.dumps(decide(cache, _reference()), sort_keys=True)
    calls = []

    def counting(cfg, width, seed, steps, device):
        calls.append(seed)
        return _fake_snapshot(cfg, width, seed, steps, device)

    cache2 = run_phase_a(CFG, torch.device("cpu"), snapshot_fn=counting,
                         preloaded=(cache["cells"][0],))
    assert 1337 not in calls and len(cache2["cells"]) == 3
    report = build_report(cache2, _reference(), decide(cache2, _reference()))
    assert any(line.startswith("decision=") for line in summarize(report))


def test_plot_result_writes_figure(tmp_path):
    cache = _cache()
    out = tmp_path / "fig" / "grok-deep-plateau-v1285.png"
    plot_result(cache, decide(cache, _reference()), out)
    assert out.exists() and out.stat().st_size > 10_000
