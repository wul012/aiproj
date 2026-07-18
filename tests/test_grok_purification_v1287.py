"""v1287 post-grok purification: preregistered decision-logic tests.

Synthetic caches exercise every verdict branch, guard, and G0 path without
training. The REFS table repeats the committed v1285/v1286 cache values
(anchors, top-5 sets, t_gen) so the preregistered constants are themselves
regression-checked.
"""
from __future__ import annotations

from dataclasses import asdict, replace

from minigpt.grok_purification_v1287 import (
    SCHEMA,
    PurificationConfig,
    build_report,
    cell_metrics,
    decide,
    plot_result,
    run_cell,
    run_phase_a,
    step_of,
    summarize,
)

CFG = PurificationConfig()

# (lr, seed): (t_mem, t_gen, steps_run, c0, final_share, top5, heldout)
REFS = {
    (1e-3, 1337): (100, 11400, 11600, 0.106395, 0.305171, [42, 2, 47, 25, 43], 0.965989),
    (1e-3, 1338): (100, 12700, 12900, 0.11039, 0.311829, [34, 28, 13, 25, 4], 0.951906),
    (1e-3, 1339): (100, 10500, 11600, 0.110454, 0.304702, [31, 5, 38, 8, 20], 0.970772),
    (2e-3, 1337): (100, 1900, 2000, 0.103448, 0.586188, [42, 2, 43, 23, 3], 0.993889),
    (2e-3, 1338): (100, 2800, 2900, 0.112946, 0.550819, [40, 34, 13, 22, 36], 0.986582),
    (4e-3, 1337): (100, 1400, 1400, 0.10206, 0.716182, [3, 2, 43, 21, 5], 0.99442),
    (4e-3, 1338): (100, 1800, 1800, 0.111007, 0.685856, [40, 22, 21, 4, 47], 0.99907),
    (4e-3, 1339): (100, 1000, 1100, 0.108881, 0.616716, [38, 20, 31, 41, 0], 0.999203),
    (8e-3, 1337): (300, 1000, 1000, 0.108862, 0.711672, [14, 5, 13, 32, 29], 0.999336),
    (8e-3, 1338): (200, 1400, 1400, 0.10401, 0.814102, [4, 36, 8, 43, 28], 0.989106),
    (8e-3, 1339): (200, 1500, 1500, 0.105634, 0.757589, [38, 13, 20, 15, 21], 0.991497),
}


def _curve(t_gen, steps):
    return [(0, 0.0, 0.02)] + [(k, 1.0, 0.02 if k < t_gen else 0.97)
                               for k in range(100, steps + 1, 100)]


def _power(share, top5):
    power = [(1 - share) / 44] * 49
    for i in top5:
        power[i] = share / 5
    return power


def _ref_cell(lr, seed, with_lr, final=None, curve=None):
    t_mem, t_gen, steps_run, c0, cached_final, top5, heldout = REFS[(lr, seed)]
    final = cached_final if final is None else final
    cell = {"seed": seed, "t_mem": t_mem, "t_gen": t_gen,
            "steps_run": steps_run, "c0_share": c0, "final_share": final,
            "top5": top5, "heldout_acc": heldout,
            "curve": curve or _curve(t_gen, steps_run),
            "snapshots": [{"k": 100, "val_acc": 0.02,
                           "share": c0 + 0.6 * (final - c0)}]}
    return cell | {"lr": lr} if with_lr else cell


def _refs(overrides=None):
    overrides = overrides or {}
    canonical = {"cells": [_ref_cell(1e-3, s, False,
                                     **overrides.get((1e-3, s), {}))
                           for s in (1337, 1338, 1339)]}
    compressed = {"cells": [_ref_cell(lr, s, True, **overrides.get((lr, s), {}))
                            for lr, s in REFS if lr != 1e-3]}
    return canonical, compressed


def _new_cell(lr, seed, purities, curve=None):
    t_mem, t_gen, _sr, _c0, _final, top5, heldout = REFS[(lr, seed)]
    ladder = [step_of(m, t_gen) for m in CFG.multipliers]
    horizon = ladder[-1]
    curve = curve or _curve(t_gen, horizon)
    by_step = {row[0]: row for row in curve}
    snapshots = [{"k": k, "train_acc": by_step[k][1], "val_acc": by_step[k][2],
                  "power": _power(purities[i], top5), "prefix_ok": True}
                 for i, k in enumerate(ladder[:-1])]
    return {"lr": lr, "seed": seed, "t_gen_ref": t_gen, "ladder": ladder,
            "steps_run": horizon, "t_mem": t_mem, "t_gen": t_gen,
            "heldout_acc": heldout, "curve": curve,
            "final_power": _power(purities[-1], top5),
            "prefix_ok": True, "snapshots": snapshots}


BENIGN = {2e-3: (0.82, 0.86, 0.89, 0.9), 4e-3: (0.82, 0.86, 0.89, 0.9),
          8e-3: (0.82, 0.86, 0.89, 0.9)}


def _cache(canonical_purities, compressed=BENIGN, per_seed=None):
    cells = []
    for lr, seed, _t in CFG.cells:
        purities = (per_seed or {}).get((lr, seed)) or \
            (canonical_purities if lr == 1e-3 else compressed[lr])
        cells.append(_new_cell(lr, seed, purities))
    return {"schema": SCHEMA, "generated_at": "t", "config": asdict(CFG),
            "cells": cells, "runs": 44, "total_steps": 407800}


def test_config_and_ladder_derivation():
    CFG.validate()
    assert [step_of(m, 11400) for m in CFG.multipliers] == \
        [16000, 20500, 27400, 34200]
    assert [step_of(m, 1000) for m in CFG.multipliers] == \
        [1400, 1800, 2400, 3000]
    for bad in (
        replace(CFG, multipliers=(1.8, 1.4, 3.0)),
        replace(CFG, grok_stop_val=0.95),
        replace(CFG, max_total_steps=100000),
        replace(CFG, max_runs=40),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


def test_verdict_branches():
    canonical, compressed = _refs()
    info = decide(_cache((0.5, 0.7, 0.85, 0.9)), canonical, compressed)
    assert (info["verdict"], info["reason"]) == ("purification_universal", "")
    assert info["g0_ok"] and info["g1_complete"] and info["g2_bar_stable"]

    info = decide(_cache((0.35, 0.4, 0.45, 0.5)), canonical, compressed)
    assert info["verdict"] == "partial_purification"

    info = decide(_cache((0.31, 0.31, 0.312, 0.313)), canonical, compressed)
    assert info["verdict"] == "purification_lr_gated"
    assert info["climb_by_lr"]["0.001"] < 0.05


def test_guards():
    canonical, compressed = _refs()
    info = decide(_cache((0.55, 0.45, 0.5, 0.55)), canonical, compressed)
    assert (info["verdict"], info["reason"]) == ("review", "purity_regression")

    per_seed = {(1e-3, 1337): (0.5, 0.6, 0.7, 0.8),
                (1e-3, 1338): (0.31, 0.315, 0.315, 0.316),
                (1e-3, 1339): (0.4, 0.45, 0.5, 0.55)}
    info = decide(_cache(None, per_seed=per_seed), canonical, compressed)
    assert (info["verdict"], info["reason"]) == ("review", "mixed_seeds")

    info = decide(_cache((0.35, 0.36, 0.37, 0.385)), canonical, compressed)
    assert (info["verdict"], info["reason"]) == ("review",
                                                "climb_bar_instability")
    assert not info["g2_bar_stable"]

    flat = {key: {"final": 0.31} for key in REFS}
    canonical_flat, compressed_flat = _refs(flat)
    info = decide(_cache((0.31, 0.31, 0.31, 0.315),
                         compressed={lr: (0.31, 0.31, 0.31, 0.315)
                                     for lr in (2e-3, 4e-3, 8e-3)}),
                  canonical_flat, compressed_flat)
    assert (info["verdict"], info["reason"]) == ("review",
                                                "unexpected_geometry")


def test_g0_paths():
    canonical, compressed = _refs()

    cache = _cache((0.5, 0.7, 0.85, 0.9))
    cache["cells"][0]["prefix_ok"] = False
    assert decide(cache, canonical, compressed)["reason"] == \
        "prefix_nondeterministic"

    cache = _cache((0.5, 0.7, 0.85, 0.9))
    cache["cells"][0]["steps_run"] -= 100
    assert decide(cache, canonical, compressed)["reason"] == "early_stop_fired"

    cache = _cache((0.5, 0.7, 0.85, 0.9))
    cache["cells"][0]["t_gen"] += 100
    assert decide(cache, canonical, compressed)["reason"] == \
        "reference_mismatch"

    cache = _cache((0.5, 0.7, 0.85, 0.9))
    step, train, val = cache["cells"][0]["curve"][5]
    cache["cells"][0]["curve"][5] = (step, train, val + 0.001)
    assert decide(cache, canonical, compressed)["reason"] == \
        "reference_mismatch"

    cache = _cache((0.5, 0.7, 0.85, 0.9))
    cache["cells"][0]["heldout_acc"] = 0.5
    assert decide(cache, canonical, compressed)["reason"] == \
        "substrate_unsound"

    coupled = [(0, 0.0, 0.0)] + [(k, 1.0, 0.96) for k in range(100, 34201, 100)]
    canonical_c, compressed_c = _refs({(1e-3, 1337): {"curve": coupled[:117]}})
    cache = _cache((0.5, 0.7, 0.85, 0.9))
    cache["cells"][0] = _new_cell(1e-3, 1337, (0.5, 0.7, 0.85, 0.9),
                                  curve=coupled)
    assert decide(cache, canonical_c, compressed_c)["reason"] == \
        "phase_mismatch"

    cache = _cache((0.5, 0.7, 0.85, 0.9))
    cache["cells"].pop()
    info = decide(cache, canonical, compressed)
    assert (info["verdict"], info["reason"]) == ("review", "grid_incomplete")


def test_phase_a_orchestration_and_budget():
    calls = []

    def fake(cfg, seed, steps, horizon, device):
        calls.append((cfg.lr, seed, steps))
        t_mem, t_gen, _sr, _c0, _final, top5, heldout = REFS[(cfg.lr, seed)]
        curve = _curve(t_gen, steps)
        last = curve[-1]
        out = {"steps": steps, "train_acc": last[1], "val_acc": last[2],
               "power": _power(0.5, top5)}
        if steps >= horizon:
            out |= {"t_mem": t_mem, "t_gen": t_gen, "heldout_acc": heldout,
                    "curve": curve}
        return out

    cache = run_phase_a(CFG, None, snapshot_fn=fake)
    assert len(calls) == 44 and cache["runs"] == 44
    assert cache["total_steps"] == 407800
    assert [(c["lr"], c["seed"]) for c in cache["cells"]] == \
        [(lr, seed) for lr, seed, _t in CFG.cells]

    probe = run_cell(CFG, 8e-3, 1337, 1000, None, snapshot_fn=fake)
    assert probe["ladder"] == [1400, 1800, 2400, 3000]
    calls.clear()
    cache = run_phase_a(CFG, None, snapshot_fn=fake, preloaded=(probe,))
    assert len(calls) == 40 and cache["runs"] == 44


def test_metrics_report_and_figure(tmp_path):
    canonical, compressed = _refs()
    ref = canonical["cells"][0]
    rotated = _new_cell(1e-3, 1337, (0.5, 0.7, 0.85, 0.9))
    rotated["final_power"] = _power(0.9, [0, 1, 3, 6, 7])
    metrics = cell_metrics(rotated, ref, CFG)
    assert not metrics["set_match"]
    assert abs(metrics["own_final"] - 0.9) < 1e-6
    assert metrics["c_final"] < 0.1

    cache = _cache((0.5, 0.7, 0.85, 0.9))
    info = decide(cache, canonical, compressed)
    report = build_report(cache, canonical, compressed, info)
    assert report["schema"] == SCHEMA and len(report["cells"]) == 11
    row = report["cells"][0]
    assert abs(row["climb"] - (0.9 - 0.305171)) < 1e-6
    assert abs(row["f_ext"] - 0.1503) < 0.02
    assert row["set_match"] and not row["saturated"]  # 0.85 -> 0.9 still moving
    slowed = _new_cell(1e-3, 1337, (0.5, 0.7, 0.895, 0.9))
    assert cell_metrics(slowed, ref, CFG)["saturated"]
    assert "f_ext_unified" in report["summary"]
    lines = summarize(report)
    assert lines[0].startswith("decision=purification_universal")

    out = tmp_path / "fig.png"
    plot_result(cache, canonical, compressed, info, out)
    assert out.exists()
