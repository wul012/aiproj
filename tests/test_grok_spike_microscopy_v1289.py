"""v1289 spike microscopy: preregistered decision-logic tests.

Synthetic dense-window caches exercise episode extraction/qualification, the
r-statistic and labels, every verdict branch, the G0/G1/G2 guards, and the
Phase-A budget/preload accounting without training. Pytest-style but
pytest-import-free (the CI unit-test runner is plain unittest without
pytest installed).
"""
from __future__ import annotations

from dataclasses import replace

import torch

from minigpt.grok_spike_microscopy_v1289 import (
    SCHEMA,
    SpikeMicroscopyConfig,
    build_report,
    decide,
    extract_episodes,
    plot_result,
    run_phase_a,
    summarize,
)

CFG = SpikeMicroscopyConfig()

CONC = [0.18] * 5 + [0.1 / 43] * 43          # top-5 share 0.9
UNIFORM = [1.0 / 48] * 48                     # top-5 share 5/48
MID = [0.117] * 5 + [0.415 / 43] * 43         # top-5 share 0.585 -> r 0.65
POWERS = {"conc": CONC, "uniform": UNIFORM, "mid": MID}


def _val_at(step, dips, healthy=0.95):
    for d in dips:
        if d[0] <= step <= d[1]:
            return d[2]
    return healthy


def _power_at(step, dips):
    for d in dips:
        if d[0] <= step <= d[1] and len(d) > 3:
            return POWERS[d[3]]
    return CONC


def _block(w0, w1, dips=(), power_glitch=None):
    steps = list(range(w0, w1 + 1))
    power = [list(_power_at(s, dips)) for s in steps]
    if power_glitch is not None:
        power[power_glitch - w0] = list(UNIFORM)
    return {"w0": w0, "w1": w1, "steps": steps,
            "train_acc": [1.0] * len(steps),
            "val_acc": [_val_at(s, dips) for s in steps],
            "train_loss": [1e-4] * len(steps),
            "grad_norm": [1.0] * len(steps),
            "norm": [10.0] * len(steps),
            "power": torch.tensor(power, dtype=torch.float32)}


def _cell(lr, seed, rerun_end, blocks):
    def at(s):
        for b in blocks:
            if b["w0"] <= s <= b["w1"]:
                i = s - b["w0"]
                return (round(b["train_acc"][i], 6),
                        round(b["val_acc"][i], 6))
        return (1.0, 0.95)
    coarse = [(s,) + at(s) for s in range(0, rerun_end + 1, 100)]
    return {"lr": lr, "seed": seed, "rerun_end": rerun_end,
            "windows": [[b["w0"], b["w1"]] for b in blocks],
            "coarse": coarse, "dense": blocks}


def _wrap(cfg, cells):
    cache = {"schema": SCHEMA, "generated_at": "t", "config": {},
             "cells": cells, "runs": len(cells),
             "total_steps": sum(c[2] for c in cfg.cells)}
    ref = {"schema": "grok_purification_v1287.v1",
           "cells": [{"lr": c["lr"], "seed": c["seed"],
                      "curve": [tuple(r) for r in c["coarse"]]}
                     for c in cells]}
    return cache, ref


def _single(dips, w0=100, w1=1400, lr=1e-3, seed=1, glitch=None):
    cfg = replace(CFG, cells=((lr, seed, w1, ((w0, w1),)),))
    cell = _cell(lr, seed, w1, [_block(w0, w1, dips, power_glitch=glitch)])
    cache, ref = _wrap(cfg, [cell])
    return cfg, cache, ref


def test_config_validate_governs_windows_and_budget():
    CFG.validate()
    assert sum(c[2] for c in CFG.cells) == 73700
    assert sum(w1 - w0 + 1 for _l, _s, _r, ws in CFG.cells
               for w0, w1 in ws) == 15620
    bad = [
        replace(CFG, cells=((1e-3, 1, 600, ((100, 400), (300, 600))),)),
        replace(CFG, cells=((1e-3, 1, 600, ((150, 600),)),)),
        replace(CFG, cells=((1e-3, 1, 700, ((100, 600),)),)),
        replace(CFG, max_total_steps=100),
        replace(CFG, max_dense_steps=100),
        replace(CFG, smooth_window=4),
        replace(CFG, deep_bar=0.7),
        replace(CFG, grok_stop_val=0.95),
        replace(CFG, min_baseline=0),
    ]
    for cfg in bad:
        try:
            cfg.validate()
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError: {cfg}")


def test_episode_qualification_rules():
    # window 1: start-truncated tail, one interior episode, end-censored tail
    b1 = _block(100, 700, dips=((100, 249, 0.2), (520, 540, 0.3),
                                (680, 700, 0.2)))
    # window 2: two interior episodes whose baselines are too short
    b2 = _block(800, 1200, dips=((810, 999, 0.3), (1020, 1040, 0.3)))
    cfg = replace(CFG, cells=((1e-3, 1, 1200, ((100, 700), (800, 1200))),))
    cell = _cell(1e-3, 1, 1200, [b1, b2])
    cache, _ref = _wrap(cfg, [cell])
    rows, excluded = extract_episodes(cache, cfg)
    assert excluded == {"edge_truncated": 2, "short_baseline": 2}
    assert len(rows) == 1
    ep = rows[0]
    assert (ep["start"], ep["end"]) == (520, 540)
    assert abs(ep["min_val"] - 0.3) < 1e-9
    assert 520 <= ep["argmin"] <= 540
    assert ep["fall"] + ep["recovery"] == ep["duration"] + 1
    assert ep["coarse_min"] is None  # invisible at the 100-step grid


def test_r_statistic_labels_and_smoothing():
    dips = ((400, 420, 0.2, "conc"), (700, 720, 0.2, "uniform"),
            (1000, 1020, 0.2, "mid"))
    cfg, cache, _ref = _single(dips, glitch=350)
    rows, _exc = extract_episodes(cache, cfg)
    assert [e["label"] for e in rows] == ["preserved", "destroyed", "mid"]
    pres, dest, mid = rows
    assert abs(pres["r"] - 1.0) < 1e-6
    # the single-step glitch at 350 must not drag the median baseline
    assert abs(pres["baseline_share"] - 0.9) < 0.02
    assert abs(dest["r"] - (5 / 48) / 0.9) < 1e-3
    assert abs(mid["r"] - 0.65) < 1e-2
    assert pres["set_rotated"] is False


def test_decide_verdict_ladder():
    def dips(kind):
        return tuple((s, s + 20, 0.2, kind) for s in (400, 700, 1000))
    cases = [
        (dips("conc"), "spike_preserves_circuit", ""),
        (dips("uniform"), "spike_destroys_circuit", ""),
        (((400, 420, 0.2, "conc"), (700, 720, 0.2, "uniform"),
          (1000, 1020, 0.2, "uniform")), "spike_mixed", ""),
        (dips("mid"), "review", "mid_band"),
        (((400, 420, 0.2, "conc"), (700, 720, 0.2, "conc")),
         "review", "insufficient_deep"),
    ]
    for dip_spec, verdict, reason in cases:
        cfg, cache, ref = _single(dip_spec)
        info = decide(cache, ref, cfg)
        assert info["g0_ok"] and info["g1_complete"], (verdict, info)
        assert info["verdict"] == verdict, (verdict, info)
        assert info["reason"] == reason, (reason, info)
    info = decide(*_single(dips("conc"))[1:], replace(
        CFG, cells=((1e-3, 1, 1400, ((100, 1400),)),)))
    assert info["n_deep"] == 3 and info["n_preserved"] == 3


def test_decide_g0_g1_g2_guards():
    dips = tuple((s, s + 20, 0.2, "conc") for s in (400, 700, 1000))
    cfg, cache, ref = _single(dips)
    bad_ref = {"cells": [dict(ref["cells"][0])]}
    bad_ref["cells"][0]["curve"] = [
        (s, t, v + 0.01 if s == 200 else v)
        for s, t, v in ref["cells"][0]["curve"]]
    info = decide(cache, bad_ref, cfg)
    assert (info["verdict"], info["reason"]) == ("review",
                                                 "reference_mismatch")
    cfg2, cache2, ref2 = _single(dips)
    cache2["cells"][0]["dense"][0]["steps"] = \
        cache2["cells"][0]["dense"][0]["steps"][:-1]
    info = decide(cache2, ref2, cfg2)
    assert (info["verdict"], info["reason"]) == ("review", "grid_incomplete")
    cfg3, cache3, ref3 = _single(dips)
    cache3["cells"][0]["dense"][0]["val_acc"][300 - 100] = 0.5  # step 300
    info = decide(cache3, ref3, cfg3)
    assert (info["verdict"], info["reason"]) == ("review",
                                                 "dense_coarse_mismatch")
    # G2: three deep preserved dips + two 0.58-floor destroyed dips that only
    # become deep at bar 0.6 -> label flips preserves -> mixed across the grid
    flip = (tuple((s, s + 20, 0.45, "conc") for s in (400, 700, 1000))
            + ((1300, 1320, 0.58, "uniform"), (1600, 1620, 0.58, "uniform")))
    cfg4, cache4, ref4 = _single(flip, w1=2000)
    info = decide(cache4, ref4, cfg4)
    assert (info["verdict"], info["reason"]) == ("review", "bar_instability")
    assert len(set(info["verdict_by_bar"].values())) > 1


def test_run_phase_a_budget_and_preload():
    calls = []

    def fake_dense(cfg, lr, seed, rerun_end, windows, device):
        calls.append((lr, seed))
        return {"lr": lr, "seed": seed, "rerun_end": rerun_end,
                "windows": [list(w) for w in windows], "coarse": [],
                "dense": []}

    preloaded = ({"lr": 8e-3, "seed": 1338, "rerun_end": 3500,
                  "windows": [[1100, 2300], [2800, 3500]], "coarse": [],
                  "dense": []},)
    cache = run_phase_a(CFG, device=None, dense_fn=fake_dense,
                        preloaded=preloaded)
    assert len(calls) == 8 and (8e-3, 1338) not in calls
    assert cache["runs"] == 9
    assert cache["total_steps"] == 73700
    assert [(c["lr"], c["seed"]) for c in cache["cells"]] \
        == [(lr, seed) for lr, seed, _r, _w in CFG.cells]


def test_report_summarize_and_plot(tmp_path):
    dips = ((400, 420, 0.2, "conc"), (700, 720, 0.2, "conc"),
            (1000, 1020, 0.2, "conc"))
    cfg, cache, ref = _single(dips)
    info = decide(cache, ref, cfg)
    report = build_report(cache, ref, info, cfg)
    assert report["schema"] == SCHEMA
    s = report["summary"]
    assert s["verdict"] == "spike_preserves_circuit" and s["status"] == "pass"
    assert s["n_deep"] == 3 and s["runs"] == 1
    assert s["hidden_depth_median"] is None or s["hidden_depth_median"] >= 0
    assert len(report["episodes"]) == 3
    lines = summarize(report)
    assert lines and "spike_preserves_circuit" in lines[0]
    out = tmp_path / "fig.png"
    plot_result(cache, info, out)
    assert out.exists() and out.stat().st_size > 0
