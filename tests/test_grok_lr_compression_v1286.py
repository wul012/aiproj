"""v1286 gate tests: config validation, all G0 paths, all four ladder branches
plus both dispersion guards and bar instability, orchestration with injected
snapshots + P2 preload, byte-stable contract, figure smoke."""
from __future__ import annotations

import json

import torch

from minigpt.grok_lr_compression_v1286 import (
    LrCompressionConfig,
    build_report,
    decide,
    plot_result,
    run_phase_a,
    summarize,
)

CFG = LrCompressionConfig()
REFS = {(2e-3, 1337): (100, 1900, 0.993889), (2e-3, 1338): (100, 2800, 0.986582),
        (4e-3, 1337): (100, 1400, 0.99442), (4e-3, 1338): (100, 1800, 0.99907),
        (4e-3, 1339): (100, 1000, 0.999203), (8e-3, 1337): (300, 1000, 0.999336),
        (8e-3, 1338): (200, 1400, 0.989106), (8e-3, 1339): (200, 1500, 0.991497)}


def _reference():
    cells = []
    for (lr, seed), (t_mem, t_gen, heldout) in REFS.items():
        cells.append({"arm": "any", "alpha": 1.0, "lr": lr, "seed": seed,
                      "t_mem": t_mem, "t_gen": t_gen, "heldout_acc": heldout})
    return {"schema": "grok_norm_vs_step_v1281.v1", "cells": cells}


def _curve3(t_gen, steps_run):
    return [(step, 1.0, 0.02 if step < t_gen else 0.97)
            for step in range(100, steps_run + 1, 100)]


def _share_sculpt(k, t_gen):
    return 0.1 + 0.7 * min(1.0, 1.2 * k / t_gen)


def _share_late(k, t_gen):
    return 0.1


def _share_partial(k, t_gen):
    return 0.1 + 0.245 * min(1.0, k / t_gen)


def _cell(lr, seed, share_fn):
    t_mem, t_gen, heldout = REFS[(lr, seed)]
    steps_run = t_gen + 200
    curve = _curve3(t_gen, steps_run)
    by_step = dict((r[0], r) for r in curve)
    snapshots = []
    for k in CFG.ladder:
        if k >= steps_run:
            break
        row = by_step[k]
        snapshots.append({"k": k, "train_acc": row[1], "val_acc": row[2],
                          "share": share_fn(k, t_gen), "prefix_ok": True})
    return {"width": 128, "lr": lr, "seed": seed, "expected_phase": "delayed",
            "steps_run": steps_run, "t_mem": t_mem, "t_gen": t_gen,
            "heldout_acc": heldout, "curve": curve, "top5": [0, 1, 2, 3, 4],
            "final_share": 0.8, "c0_share": 0.1, "prefix_ok": True,
            "snapshots": snapshots}


def _cache(share_fn=_share_sculpt, per_lr=None, tweaks=()):
    cells = []
    for lr, seeds in CFG.cells:
        fn = (per_lr or {}).get(lr, share_fn)
        for seed in seeds:
            cells.append(_cell(lr, seed, fn))
    for (lr, seed), patch in tweaks:
        for c in cells:
            if c["lr"] == lr and c["seed"] == seed:
                c.update(patch)
    return {"schema": "grok_lr_compression_v1286.v1", "generated_at": "t",
            "config": {}, "cells": cells, "runs": 100, "total_steps": 100000}


# ------------------------------------------------------------------ units ----
def test_config_validation():
    for bad in (
        LrCompressionConfig(width=130),
        LrCompressionConfig(ladder=(100, 250)),
        LrCompressionConfig(pre_bar=0.3),
        LrCompressionConfig(cells=((2e-3, (1337,)),)),
        LrCompressionConfig(max_runs=100),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------- verdicts ----
def test_decide_three_main_branches():
    inv = decide(_cache(), _reference())
    assert inv["verdict"] == "construction_completion_invariant"
    assert inv["g0_ok"] and inv["g1_complete"] and inv["g2_bar_stable"]
    late = decide(_cache(_share_late), _reference())
    assert late["verdict"] == "compression_switches_to_late_construction"
    partial = decide(_cache(_share_partial), _reference())
    assert partial["verdict"] == "partial_under_compression"


def test_decide_dispersion_guards_and_bar_instability():
    mixed_lrs = decide(_cache(per_lr={2e-3: _share_sculpt, 4e-3: _share_late,
                                      8e-3: _share_late}), _reference())
    assert mixed_lrs["verdict"] == "review" and mixed_lrs["reason"] == "mixed_lrs"
    cache = _cache(_share_partial)
    for c in cache["cells"]:
        if c["lr"] == 4e-3 and c["seed"] == 1337:
            for s in c["snapshots"]:
                s["share"] = 0.1
        if c["lr"] == 4e-3 and c["seed"] == 1338:
            for s in c["snapshots"]:
                s["share"] = 0.75
    mixed_seeds = decide(cache, _reference())
    assert mixed_seeds["reason"] == "mixed_seeds"
    # a graded final approach makes t_pre bar-dependent with shares crossing bins
    ramp = _cache(_share_late)
    for c in ramp["cells"]:
        snaps = c["snapshots"]
        snaps[-3]["val_acc"], snaps[-3]["share"] = 0.08, 0.15
        snaps[-2]["val_acc"], snaps[-2]["share"] = 0.13, 0.35
        snaps[-1]["val_acc"], snaps[-1]["share"] = 0.18, 0.6
    assert decide(ramp, _reference())["reason"] == "bar_instability"


def test_decide_g0_paths():
    bad_prefix = decide(_cache(tweaks=(((4e-3, 1337), {"prefix_ok": False}),)),
                        _reference())
    assert bad_prefix["reason"] == "prefix_nondeterministic"
    bad_ref = decide(_cache(tweaks=(((4e-3, 1337), {"t_gen": 1500}),)),
                     _reference())
    assert bad_ref["reason"] == "reference_mismatch"
    coupled_curve = [(step, min(1.0, 0.3 + step / 1000),
                      min(0.97, 0.28 + step / 1000))
                     for step in range(100, 1601, 100)]
    swapped = decide(_cache(tweaks=(((4e-3, 1337), {"curve": coupled_curve}),)),
                     _reference())
    assert swapped["reason"] == "phase_mismatch"
    incomplete = _cache()
    incomplete["cells"][0]["snapshots"] = incomplete["cells"][0]["snapshots"][:-1]
    assert decide(incomplete, _reference())["reason"] == "grid_incomplete"


# ------------------------------------------------------- orchestration/etc ----
def _fake_snapshot(cfg, width, seed, steps, device):
    t_mem, t_gen, heldout = REFS[(cfg.lr, seed)]
    steps_run = min(steps, t_gen + 200)
    curve = _curve3(t_gen, steps_run)
    last = curve[-1]
    tp = 0.8 if steps_run >= t_gen else _share_partial(steps_run, t_gen)
    power = [tp / 5] * 5 + [(1 - tp) / 43] * 43
    out = {"steps": steps_run, "train_acc": last[1], "val_acc": last[2],
           "power": power}
    if steps >= cfg.max_steps:
        out |= {"t_mem": t_mem, "t_gen": t_gen, "heldout_acc": heldout,
                "curve": curve}
    return out


def test_run_phase_a_with_injected_snapshots_and_preload():
    cache = run_phase_a(CFG, torch.device("cpu"), snapshot_fn=_fake_snapshot)
    assert len(cache["cells"]) == 8
    info = decide(cache, _reference())
    assert info["verdict"] == "partial_under_compression"
    assert json.dumps(info, sort_keys=True) == \
        json.dumps(decide(cache, _reference()), sort_keys=True)
    calls = []

    def counting(cfg, width, seed, steps, device):
        calls.append((cfg.lr, seed))
        return _fake_snapshot(cfg, width, seed, steps, device)

    cache2 = run_phase_a(CFG, torch.device("cpu"), snapshot_fn=counting,
                         preloaded=(cache["cells"][0],))
    assert (2e-3, 1337) not in calls and len(cache2["cells"]) == 8
    report = build_report(cache2, _reference(), decide(cache2, _reference()))
    assert any(line.startswith("decision=") for line in summarize(report))


def test_plot_result_writes_figure(tmp_path):
    cache = _cache()
    out = tmp_path / "fig" / "grok-lr-compression-v1286.png"
    plot_result(cache, decide(cache, _reference()), out)
    assert out.exists() and out.stat().st_size > 10_000
