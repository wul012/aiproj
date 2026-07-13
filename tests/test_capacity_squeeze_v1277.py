"""v1277 gate tests: metric correctness on constructed embeddings, every decide()
branch on synthetic caches, config validation, real-model cell metrics, and the
byte-stable contract over a cached run."""
from __future__ import annotations

import json
import math

import torch

from minigpt.capacity_squeeze_v1277 import (
    SqueezeConfig,
    build_report,
    cell_metrics,
    classify_cell,
    decide,
    feature_directions,
    gram_offdiag,
    k_func_of,
    participation_ratio,
    run_phase_a,
    summarize,
    top_freqs,
)
from minigpt.grok_checkpoint_v1185 import CheckpointMeta
from minigpt.grok_v1179 import GrokConfig, make_grok_model

P = 97


def _meta(width: int = 8, seed: int = 1337) -> CheckpointMeta:
    return CheckpointMeta(
        p=P, train_frac=0.2, seed=seed, weight_decay=1.0, vocab_size=P + 2,
        n_layer=1, n_head=4, n_embd=width, block_size=5, t_mem=100, t_gen=15000,
        final_train_acc=1.0, final_val_acc=0.95, steps_run=16000,
    )


def _cell(width, seed, heldout, keep_accs, maxcos=0.05):
    return {
        "width": width, "seed": seed, "steps_run": 16000, "t_mem": 100,
        "t_gen": 15000, "final_train_acc": 1.0, "final_val_acc": heldout,
        "heldout_acc": heldout, "power": [1.0 / 48] * 48,
        "top_freqs": list(range(1, 9)), "keep_accs": keep_accs,
        "gram_by_k": {k: {"maxcos": maxcos, "meansq": maxcos**2} for k in range(1, 9)},
        "n_eff": 5.0,
    }


def _keep(k_reach: int | None, heldout: float = 0.95) -> list[float]:
    """A keep-ablation curve that first reaches 0.95*heldout at k=k_reach."""
    if k_reach is None:
        return [0.1] * 8
    return [0.1] * (k_reach - 1) + [heldout] * (9 - k_reach)


def _cache(cells):
    return {"schema": "capacity_squeeze_v1277.v1", "generated_at": "t",
            "config": {}, "cells": cells}


def _grid(squeeze_class: str, base_k: int = 4) -> list[dict]:
    """A full 15-cell synthetic grid whose squeeze cells have the given class."""
    cells = []
    for width in (32, 16, 12):
        for seed in (1, 2, 3):
            cells.append(_cell(width, seed, 0.95, _keep(base_k)))
    for width in (8, 4):
        for seed in (1, 2, 3):
            if squeeze_class == "not_grokked":
                cells.append(_cell(width, seed, 0.30, _keep(None, 0.30)))
            elif squeeze_class == "forced_packing":
                cells.append(_cell(width, seed, 0.95, _keep(5), maxcos=0.6))
            elif squeeze_class == "economized":
                cells.append(_cell(width, seed, 0.95, _keep(width // 4)))
            elif squeeze_class == "off_mechanism":
                cells.append(_cell(width, seed, 0.95, _keep(None)))
    return cells


# ------------------------------------------------------------------ metrics --
def test_participation_ratio_point_mass_and_uniform():
    point = torch.zeros(48)
    point[7] = 1.0
    assert math.isclose(participation_ratio(point), 1.0, rel_tol=1e-6)
    uniform = torch.full((48,), 1.0 / 48)
    assert math.isclose(participation_ratio(uniform), 48.0, rel_tol=1e-6)
    assert participation_ratio(torch.zeros(4)) == 0.0


def test_feature_directions_recover_orthogonal_planted_freqs():
    ks = torch.arange(P, dtype=torch.float32)
    cols = [torch.cos(2 * torch.pi * 5 * ks / P), torch.sin(2 * torch.pi * 5 * ks / P),
            torch.cos(2 * torch.pi * 11 * ks / P), torch.sin(2 * torch.pi * 11 * ks / P)]
    E = torch.stack(cols, dim=1)  # (p, 4): two exact frequencies, orthogonal planes
    dirs = feature_directions(E, [5, 11], P)
    assert dirs.shape == (4, 4)
    stats = gram_offdiag(dirs)
    assert stats["maxcos"] < 1e-3
    spectrum_top = top_freqs(torch.tensor(
        [0.0] * 4 + [1.0] + [0.0] * 5 + [1.0] + [0.0] * 37), 2)
    assert set(spectrum_top) == {5, 11}


def test_gram_offdiag_detects_duplicated_direction():
    v = torch.tensor([[1.0, 0.0], [1.0, 0.0]])
    stats = gram_offdiag(v)
    assert stats["maxcos"] > 0.999


def test_k_func_of_thresholds_and_none():
    accs = [0.2, 0.5, 0.86, 0.94, 0.97, 0.98, 0.98, 0.99]
    assert k_func_of(accs, 0.96, 0.90) == 4  # bar 0.864 -> k=4 (0.94)
    assert k_func_of(accs, 0.96, 0.85) == 3  # bar 0.816 -> k=3 (0.86)
    assert k_func_of([0.1] * 8, 0.96, 0.90) is None


# ----------------------------------------------------------- classification --
def test_classify_cell_branches():
    cfg = SqueezeConfig()
    assert classify_cell(_cell(8, 1, 0.30, _keep(None, 0.3)), cfg, 0.9) == "not_grokked"
    assert classify_cell(_cell(8, 1, 0.95, _keep(None)), cfg, 0.9) == "off_mechanism"
    assert classify_cell(_cell(8, 1, 0.95, _keep(5)), cfg, 0.9) == "forced_packing"
    assert classify_cell(_cell(8, 1, 0.95, _keep(4)), cfg, 0.9) == "economized"


def test_decide_superposition_and_drop_branches():
    forced = decide(_cache(_grid("forced_packing")))
    assert forced["verdict"] == "squeeze_forces_superposition"
    assert forced["g0_substrate"] and forced["g1_complete"] and forced["g2_ratio_stable"]
    econ = decide(_cache(_grid("economized")))
    assert econ["verdict"] == "squeeze_drops_features"


def test_decide_floor_offmech_and_substrate_branches():
    floor = decide(_cache(_grid("not_grokked")))
    assert floor["verdict"] == "squeeze_hits_capacity_floor"
    assert floor["smallest_grokking_width"] == 12
    offm = decide(_cache(_grid("off_mechanism")))
    assert offm["verdict"] == "review"
    broken = _grid("forced_packing")
    for cell in broken:
        if cell["width"] == 32:
            cell["heldout_acc"] = 0.2
    unsound = decide(_cache(broken))
    assert unsound["verdict"] == "review" and unsound["reason"] == "substrate_unsound"
    incomplete = decide(_cache(_grid("forced_packing")[:-1]))
    assert incomplete["reason"] == "grid_incomplete"


def test_decide_ratio_instability_routes_review():
    cells = _grid("forced_packing")
    for cell in cells:
        if cell["width"] in (8, 4):
            # reaches the bar at k=5 for ratio<=0.90 but at k=2 for ratio=0.95:
            # ratio grid disagreement -> review
            cell["keep_accs"] = [0.1, 0.93, 0.93, 0.93, 0.93, 0.95, 0.95, 0.95]
            cell["heldout_acc"] = 0.95
    # ratio 0.85 bar=0.8075 -> k=2 (econ for w=8? 2*2<=8 econ; w=4: 4<=4 econ)
    # ratio 0.95 bar=0.9025 -> k=2 (0.93 >= 0.9025) still k=2 ... make it flip:
    for cell in cells:
        if cell["width"] in (8, 4):
            cell["keep_accs"] = [0.1, 0.85, 0.85, 0.85, 0.93, 0.93, 0.93, 0.93]
    # ratio .85 bar .8075 -> k=2 econ ; ratio .90 bar .855 -> k=5 forced ; flip
    out = decide(_cache(cells))
    assert out["g2_ratio_stable"] is False
    assert out["verdict"] == "review" and out["reason"] == "ratio_unstable"


def test_config_validation_rejects_bad_grids():
    for bad in (
        SqueezeConfig(widths=(30, 16, 12, 8, 4)),
        SqueezeConfig(squeeze_widths=(8, 6)),
        SqueezeConfig(baseline_width=64),
        SqueezeConfig(seeds=tuple(range(10))),
        SqueezeConfig(keep_ratio=0.8),
    ):
        try:
            bad.validate()
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


# ------------------------------------------------------- real model + cache --
def test_cell_metrics_on_untrained_tiny_model():
    cfg = SqueezeConfig()
    width = 8
    model = make_grok_model(P + 2, GrokConfig(n_embd=width, n_head=4, seeds=(1,), wds=(1.0,)))
    cell = cell_metrics(model, _meta(width), cfg)
    assert cell["width"] == width and len(cell["power"]) == 48
    assert len(cell["keep_accs"]) == 8 and len(cell["gram_by_k"]) == 8
    assert 0.0 <= cell["heldout_acc"] <= 0.2  # untrained ~ chance
    assert classify_cell(cell, cfg, cfg.keep_ratio) == "not_grokked"


def test_run_phase_a_with_injected_trainer_and_contract():
    cfg = SqueezeConfig()

    def fake_trainer(cfg_, width, seed, device):
        return object(), _meta(width, seed), []

    def fake_metrics(model, meta, cfg_):
        squeezed = meta.n_embd in cfg.squeeze_widths
        return _cell(meta.n_embd, meta.seed, 0.95, _keep(5),
                     maxcos=0.5 if squeezed else 0.05)

    cache = run_phase_a(cfg, torch.device("cpu"), trainer=fake_trainer, metrics=fake_metrics)
    assert len(cache["cells"]) == 15
    first = json.dumps(decide(cache), sort_keys=True)
    second = json.dumps(decide(cache), sort_keys=True)
    assert first == second  # byte-stable re-derivation
    report = build_report(cache, decide(cache))
    lines = summarize(report)
    assert any(line.startswith("decision=") for line in lines)
    assert report["decision"] == "squeeze_forces_superposition"
