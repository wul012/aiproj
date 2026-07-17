"""v1284 gate tests: structure-fraction math (clipping, missing t_pre),
prefix/phase/substrate G0 paths, config validation, every ladder branch incl.
the endpoint override, orchestration with an injected snapshot function and a
preloaded P2 cell, byte-stable contract, figure smoke."""
from __future__ import annotations

import json

import torch

from minigpt.grok_circuit_timing_v1284 import (
    TimingConfig,
    build_report,
    decide,
    plot_result,
    run_phase_a,
    structure_fraction,
    summarize,
)

CFG = TimingConfig()


def _curve(phase: str, steps_run: int):
    rows = []
    for step in range(100, steps_run + 1, 100):
        if phase == "delayed":
            train = min(1.0, step / 300)
            val = 0.02 if step < 2400 else 0.97  # absolute: prefix-deterministic
        else:
            val = max(0.02, min(0.97, (step - 200) / 800))
            train = min(1.0, val + 0.25)
        rows.append((step, train, val))
    return rows


def _cell(width, seed, phase, share_fn, steps_run=3000, final_share=0.8,
          c0=0.1, heldout=0.95, prefix_ok=True):
    curve = _curve(phase, steps_run)
    by_step = dict((r[0], r) for r in curve)
    snapshots = []
    for k in CFG.ladder:
        if k >= steps_run:
            break
        row = by_step[k]
        snapshots.append({"k": k, "train_acc": row[1], "val_acc": row[2],
                          "share": share_fn(k), "prefix_ok": prefix_ok})
    t_mem = next((r[0] for r in curve if r[1] >= 0.99), None)
    t_gen = next((r[0] for r in curve if r[2] >= 0.90), None)
    return {"width": width, "seed": seed, "expected_phase": phase,
            "steps_run": steps_run, "t_mem": t_mem, "t_gen": t_gen,
            "heldout_acc": heldout, "curve": curve, "top5": [0, 1, 2, 3, 4],
            "final_share": final_share, "c0_share": c0,
            "prefix_ok": prefix_ok, "snapshots": snapshots}


def _share_slow(k):        # structure builds during the plateau
    return 0.1 + 0.7 * min(1.0, k / 2200)


def _share_late(k):        # structure arrives only at the end
    return 0.1 if k < 2400 else 0.8


def _share_coupled(k):     # structure tracks val (which rises from step ~200)
    val = max(0.02, min(0.97, (k - 200) / 800))
    return 0.1 + 0.7 * val / 0.97


def _cache(delayed_share=_share_slow, coupled_share=_share_coupled,
           coupled_final=0.8, tweaks=()):
    cells = []
    for width, seed, phase in CFG.cells:
        fn = coupled_share if phase == "coupled" else delayed_share
        final = coupled_final if phase == "coupled" else 0.8
        cells.append(_cell(width, seed, phase, fn, final_share=final))
    for (width, seed), patch in tweaks:
        for c in cells:
            if c["width"] == width and c["seed"] == seed:
                c.update(patch)
    return {"schema": "grok_circuit_timing_v1284.v1", "generated_at": "t",
            "config": {}, "cells": cells, "runs": 54, "total_steps": 67800}


# ------------------------------------------------------------------ units ----
def test_structure_fraction_math():
    slow = _cell(28, 1, "delayed", _share_slow)
    assert structure_fraction(slow, 0.1) > 0.7
    coupled = _cell(20, 1, "coupled", _share_coupled)
    assert structure_fraction(coupled, 0.1) < 0.2
    # no snapshot at or below the bar -> fraction 0 by preregistration
    hot = _cell(20, 1, "coupled", _share_coupled)
    hot["snapshots"] = [s | {"val_acc": 0.5} for s in hot["snapshots"]]
    assert structure_fraction(hot, 0.1) == 0.0
    # degenerate denominator -> 0, and clipping holds
    flat = _cell(28, 1, "delayed", lambda k: 0.9, final_share=0.1, c0=0.1)
    assert structure_fraction(flat, 0.1) == 0.0


def test_config_validation():
    for bad in (
        TimingConfig(cells=CFG.cells[:5]),
        TimingConfig(ladder=(100, 250)),
        TimingConfig(ladder=(400, 100, 200)),
        TimingConfig(f_low=0.6, f_high=0.5),
        TimingConfig(pre_bar=0.3),
        TimingConfig(max_runs=50),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ---------------------------------------------------------------- verdicts ----
def test_decide_construction_and_rapid_branches():
    slow = decide(_cache())
    assert slow["verdict"] == "plateau_is_circuit_construction"
    assert slow["g0_ok"] and slow["g1_complete"] and slow["g2_bar_stable"]
    rapid = decide(_cache(delayed_share=_share_late))
    assert rapid["verdict"] == "construction_is_rapid_in_both"


def test_decide_endpoint_override_and_mixed():
    diff = decide(_cache(coupled_final=0.3))
    assert diff["verdict"] == "coupled_phase_uses_different_solution"
    mixed = decide(_cache(delayed_share=lambda k: 0.1 + 0.7 * min(1.0, k / 6000)))
    assert mixed["verdict"] == "review" and mixed["reason"] == "mixed_fractions"


def test_decide_g0_paths():
    bad_prefix = decide(_cache(tweaks=(((28, 1337), {"prefix_ok": False}),)))
    assert bad_prefix["reason"] == "prefix_nondeterministic"
    bad_heldout = decide(_cache(tweaks=(((28, 1337), {"heldout_acc": 0.5}),)))
    assert bad_heldout["reason"] == "substrate_unsound"
    swapped = decide(_cache(tweaks=(
        ((20, 1337), {"curve": _curve("delayed", 3000)}),)))
    assert swapped["reason"] == "phase_mismatch"
    incomplete = _cache()
    incomplete["cells"][0]["snapshots"] = incomplete["cells"][0]["snapshots"][:-1]
    assert decide(incomplete)["reason"] == "grid_incomplete"


# ------------------------------------------------------- orchestration/etc ----
def _fake_snapshot(cfg, width, seed, steps, device):
    phase = "delayed" if (width == 28 or (width == 24 and seed == 1338)) \
        else "coupled"
    steps_run = min(steps, 3000)
    curve = _curve(phase, steps_run)
    last = curve[-1]
    share_fn = _share_slow if phase == "delayed" else _share_coupled
    top5_power = share_fn(steps_run)
    power = [top5_power / 5] * 5 + [(1 - top5_power) / 43] * 43
    out = {"steps": steps_run, "train_acc": last[1], "val_acc": last[2],
           "power": power}
    if steps >= cfg.max_steps:
        out |= {"t_mem": next((r[0] for r in curve if r[1] >= 0.99), None),
                "t_gen": next((r[0] for r in curve if r[2] >= 0.90), None),
                "heldout_acc": 0.95,
                "curve": curve}
    return out


def test_run_phase_a_with_injected_snapshots_and_preload():
    cache = run_phase_a(CFG, torch.device("cpu"), snapshot_fn=_fake_snapshot)
    assert len(cache["cells"]) == 6
    assert cache["runs"] == 6 * 9  # full + 8 ladder points below 3000
    info = decide(cache)
    assert info["verdict"] == "plateau_is_circuit_construction"
    assert json.dumps(info, sort_keys=True) == \
        json.dumps(decide(cache), sort_keys=True)
    # preloading the first cell skips its recomputation
    calls = []

    def counting(cfg, width, seed, steps, device):
        calls.append((width, seed))
        return _fake_snapshot(cfg, width, seed, steps, device)

    pre = (cache["cells"][0],)
    cache2 = run_phase_a(CFG, torch.device("cpu"), snapshot_fn=counting,
                         preloaded=pre)
    assert (20, 1337) not in calls and len(cache2["cells"]) == 6
    report = build_report(cache2, decide(cache2))
    assert any(line.startswith("decision=") for line in summarize(report))


def test_plot_result_writes_figure(tmp_path):
    cache = _cache()
    out = tmp_path / "fig" / "grok-circuit-timing-v1284.png"
    plot_result(cache, decide(cache), out)
    assert out.exists() and out.stat().st_size > 10_000
