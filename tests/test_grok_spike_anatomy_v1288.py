"""v1288 spike anatomy: preregistered decision-logic tests.

Synthetic branch/arm/un-censor caches exercise every verdict branch, guard,
and G0 path without training. Pytest-style but pytest-import-free (the CI
unit-test runner is plain unittest without pytest installed).
"""
from __future__ import annotations

from dataclasses import replace

from minigpt.grok_spike_anatomy_v1288 import (
    SCHEMA,
    SpikeAnatomyConfig,
    build_report,
    decide,
    episodes,
    own_share,
    plot_result,
    run_phase_a,
    summarize,
)

CFG = SpikeAnatomyConfig()
CELLS = {(lr, seed): (k, h) for lr, seed, k, h in CFG.cells}


def _val_at(step, dips, healthy=1.0):
    for a, b, v in dips:
        if a <= step <= b:
            return v
    return healthy


def _ref_curve(horizon, dips=()):
    rows = [(0, 0.0, 0.02)]
    rows += [(s, 1.0, _val_at(s, dips)) for s in range(100, horizon + 1, 100)]
    return rows


def _arm_curve(rel_steps, dips=()):
    return [(s, 1.0, _val_at(s, dips)) for s in range(0, rel_steps + 1, 100)]


def _power(share):
    return [share / 5] * 5 + [(1 - share) / 44] * 44


def _reference(ref_dips=None):
    cells = []
    for (lr, seed), (_k, horizon) in CELLS.items():
        dips = (ref_dips or {}).get((lr, seed), ())
        cells.append({"lr": lr, "seed": seed,
                      "curve": _ref_curve(horizon, dips)})
    return {"schema": "grok_purification_v1287.v1", "cells": cells}


def _cell(lr, seed, wd1_dips=(), wd0_dips=(), ref_dips=()):
    k_branch, horizon = CELLS[(lr, seed)]
    rel = horizon - k_branch
    ref_rows = _ref_curve(horizon, ref_dips)
    arms = {}
    for key, dips, purity in (("wd1", wd1_dips, 0.8), ("wd0", wd0_dips, 0.6)):
        arms[key] = {"wd": 1.0 if key == "wd1" else 0.0,
                     "curve": _arm_curve(rel, dips), "power": _power(purity),
                     "norm": 8.0 if key == "wd1" else 12.0,
                     "heldout_acc": 0.99}
    return {"lr": lr, "seed": seed, "k_branch": k_branch, "horizon": horizon,
            "branch_curve": [r for r in ref_rows if r[0] <= k_branch],
            "branch_train": 1.0, "branch_val": 1.0,
            "branch_power": _power(0.6), "branch_norm": 10.0, "arms": arms}


def _cache(wd1=None, wd0=None, ref_dips=None):
    cells = [_cell(lr, seed, (wd1 or {}).get((lr, seed), ()),
                   (wd0 or {}).get((lr, seed), ()),
                   (ref_dips or {}).get((lr, seed), ()))
             for lr, seed, _k, _h in CFG.cells]
    uncensor = []
    for lr, seed, ext in CFG.uncensor:
        _kb, old = CELLS[(lr, seed)]
        dips = (ref_dips or {}).get((lr, seed), ())
        uncensor.append({"lr": lr, "seed": seed, "ext_horizon": ext,
                         "curve": _ref_curve(ext, dips),
                         "heldout_acc": 0.99})
    return {"schema": SCHEMA, "generated_at": "t", "config": {},
            "cells": cells, "uncensor": uncensor,
            "runs": 29, "total_steps": 117000}


def _dip_all(cells, offset=500, depth=0.3, width=0):
    """One deep dip per listed cell, placed offset steps into the arm."""
    return {key: ((offset, offset + width, depth),) for key in cells}


BRANCH_KEYS = [(lr, seed) for lr, seed, _k, _h in CFG.cells]


# ------------------------------------------------------------------ units ----
def test_episode_detector():
    rows = _arm_curve(2000, dips=((500, 600, 0.4), (1900, 2000, 0.2)))
    eps = episodes(rows, 0.9)
    assert len(eps) == 2
    assert eps[0] == {"start": 500, "end": 600, "min_val": 0.4,
                      "censored": False, "duration": 200}
    assert eps[1]["censored"] and eps[1]["duration"] == 200
    assert episodes(_arm_curve(2000), 0.9) == []
    assert len(episodes(rows, 0.3)) == 1  # only the 0.2 dip is below 0.3
    assert abs(own_share(_power(0.7), 5) - 0.7) < 1e-9


def test_config_validation_and_budget():
    CFG.validate()
    for bad in (
        replace(CFG, spike_bar=0.7),
        replace(CFG, arm_wds=(0.0, 1.0)),
        replace(CFG, grok_stop_val=0.95),
        replace(CFG, max_total_steps=100000),
        replace(CFG, max_runs=20),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


def test_verdict_branches():
    ref = _reference()
    driven = decide(_cache(wd1=_dip_all(BRANCH_KEYS[:8])), ref)
    assert driven["verdict"] == "spikes_are_wd_driven"
    assert driven["s1"] == 8 and driven["s0"] == 0
    assert driven["g0_ok"] and driven["g1_complete"] and driven["g2_bar_stable"]
    persist = decide(_cache(wd1=_dip_all(BRANCH_KEYS[:8]),
                            wd0=_dip_all(BRANCH_KEYS[:3])), ref)
    assert persist["verdict"] == "spikes_persist_without_wd"
    quiet = decide(_cache(), ref)
    assert quiet["verdict"] == "spikes_need_optimizer_history"
    assert quiet["purity_delta_wd1"] is not None
    assert quiet["uncensor"][0]["recovered"]


def test_review_guards():
    ref = _reference()
    mixed = decide(_cache(wd1=_dip_all(BRANCH_KEYS[:3])), ref)
    assert (mixed["verdict"], mixed["reason"]) == ("review", "mixed_evidence")
    geom = decide(_cache(wd0=_dip_all(BRANCH_KEYS[:2])), ref)
    assert (geom["verdict"], geom["reason"]) == ("review",
                                                 "unexpected_geometry")
    long_dip = decide(_cache(wd1=_dip_all(BRANCH_KEYS[:8], width=500)), ref)
    assert (long_dip["verdict"], long_dip["reason"]) == (
        "review", "atypical_morphology")
    shallow = decide(_cache(wd1=_dip_all(BRANCH_KEYS[:5], depth=0.87)), ref)
    assert (shallow["verdict"], shallow["reason"]) == (
        "review", "spike_bar_instability")


def test_g0_and_g1_paths():
    ref = _reference()
    tampered = _cache()
    tampered["cells"][0]["branch_curve"][-1] = (
        tampered["cells"][0]["branch_curve"][-1][0], 1.0, 0.5)
    assert decide(tampered, ref)["reason"] == "reference_mismatch"
    sick = _cache()
    sick["cells"][2]["branch_val"] = 0.5
    assert decide(sick, ref)["reason"] == "branch_unhealthy"
    cut = _cache()
    cut["uncensor"][0]["curve"] = cut["uncensor"][0]["curve"][:-12]
    assert decide(cut, ref)["reason"] == "reference_mismatch"
    missing = _cache()
    missing["cells"][1]["arms"].pop("wd0")
    assert decide(missing, ref)["reason"] == "grid_incomplete"
    dead_ref = _reference(ref_dips={(4e-3, 1338): ((5400, 5400, 0.43),)})
    healed = _cache(ref_dips={(4e-3, 1338): ((5400, 5400, 0.43),)})
    out = decide(healed, dead_ref)
    assert out["g0_ok"]
    assert [e["recovered"] for e in out["uncensor"]] == [True, True]


def test_phase_a_orchestration_and_preload():
    calls = {"branch": 0, "arm": 0, "uncensor": 0}

    def fake_branch(cfg, lr, seed, k_branch, device):
        calls["branch"] += 1
        return {"state": {}, "curve": [r for r in _ref_curve(k_branch)],
                "power": _power(0.6), "norm": 10.0}

    def fake_arm(cfg, lr, seed, state, steps, wd, device):
        calls["arm"] += 1
        return {"wd": wd, "curve": _arm_curve(steps), "power": _power(0.7),
                "norm": 9.0, "heldout_acc": 0.99}

    def fake_uncensor(cfg, lr, seed, ext, device):
        calls["uncensor"] += 1
        return {"lr": lr, "seed": seed, "ext_horizon": ext,
                "curve": _ref_curve(ext), "heldout_acc": 0.99}

    cache = run_phase_a(CFG, None, fake_branch, fake_arm, fake_uncensor,
                        preloaded=(_cell(4e-3, 1337),))
    assert cache["runs"] == 29 and cache["total_steps"] == 117000
    assert calls == {"branch": 8, "arm": 16, "uncensor": 2}
    assert len(cache["cells"]) == 9 and len(cache["uncensor"]) == 2


def test_report_and_figure(tmp_path):
    ref = _reference()
    cache = _cache(wd1=_dip_all(BRANCH_KEYS[:8]))
    info = decide(cache, ref)
    report = build_report(cache, ref, info)
    assert report["schema"] == SCHEMA and len(report["cells"]) == 9
    row = report["cells"][1]
    assert row["spikes_wd1"] == 1 and row["spikes_wd0"] == 0
    assert row["spikes_continuous"] == 0
    assert not row["ends_in_spike_wd1"]
    assert abs(row["purity_wd1"] - 0.8) < 1e-9
    lines = summarize(report)
    assert lines[0].startswith("decision=spikes_are_wd_driven")
    out = tmp_path / "fig.png"
    plot_result(cache, info, out)
    assert out.exists()
