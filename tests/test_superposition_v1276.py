"""Contracts for the preregistered v1276 superposition experiment."""

from __future__ import annotations

from itertools import product
from pathlib import Path

import pytest
import torch

from minigpt.superposition_v1276 import (
    SuperConfig,
    ToyAE,
    analyze,
    build_report,
    config_dict,
    decide,
    dedicated_loss,
    importance_for,
    probe_cells,
    probe_ready,
    run_phase_a,
    spearman_exact,
    weight_metrics,
)


def brute_dedicated(importances, sparsity: float, n_dims: int, points: int = 30) -> float:
    """Cartesian midpoint quadrature over a tiny independent feature distribution."""
    n = len(importances)
    support = [0.0] + [(idx + 0.5) / points for idx in range(points)]
    probs = [sparsity] + [(1.0 - sparsity) / points] * points
    keep = set(sorted(range(n), key=lambda idx: importances[idx], reverse=True)[:n_dims])
    total = 0.0
    for choices in product(range(len(support)), repeat=n):
        probability = 1.0
        loss = 0.0
        for idx, choice in enumerate(choices):
            probability *= probs[choice]
            if idx not in keep:
                loss += importances[idx] * support[choice] ** 2
        total += probability * loss
    return total


def test_dedicated_formula_matches_grid():
    importance = [1.0, 0.5, 0.2]
    analytic = dedicated_loss(importance, 0.4, 1)
    numeric = brute_dedicated(importance, 0.4, 1)
    assert analytic == pytest.approx(0.14)
    assert numeric == pytest.approx(analytic, abs=5e-5)


def test_toy_ae_shape_and_nonnegative():
    torch.manual_seed(1)
    model = ToyAE(7, 3)
    output = model(torch.rand(5, 7))
    assert output.shape == (5, 7)
    assert torch.all(output >= 0)
    assert model.weight.shape == (3, 7)


def test_weight_metrics_count_and_interference():
    weight = torch.tensor([[1.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    metrics = weight_metrics(weight, (0.3, 0.5, 0.7))
    assert metrics["represented"] == {"0.3": 3, "0.5": 3, "0.7": 3}
    assert metrics["interference"] == [1.0, 0.0, 1.0]


def test_exact_spearman_is_one_sided():
    rho, p_value = spearman_exact([1, 2, 3, 4, 5])
    assert rho == pytest.approx(1.0)
    assert p_value == pytest.approx(1.0 / 120.0)
    reversed_rho, reversed_p = spearman_exact([5, 4, 3, 2, 1])
    assert reversed_rho == pytest.approx(-1.0)
    assert reversed_p == pytest.approx(1.0)


def _cfg() -> SuperConfig:
    return SuperConfig(steps=100, rec_every=10, traj_eval_size=32, final_eval_size=64)


def _weight(cfg: SuperConfig, count: int, *, extra_norm: float = 1.0, wrong_order: bool = False) -> list:
    weight = torch.zeros(cfg.n_dims, cfg.n_features)
    indices = list(range(count))
    if wrong_order and count == cfg.n_dims:
        indices = list(range(1, cfg.n_dims + 1))
    for pos, feature in enumerate(indices):
        norm = 1.0 if pos < cfg.n_dims else extra_norm
        weight[pos % cfg.n_dims, feature] = norm
    return weight.tolist()


def synth_cache(
    *,
    counts: list[int] | None = None,
    sparse_ratio: float = 0.5,
    extra_norm: float = 1.0,
    wrong_order: bool = False,
    bad_cell: bool = False,
) -> tuple[dict, SuperConfig]:
    cfg = _cfg()
    counts = counts or [5, 6, 8, 10, 12]
    cells = {}
    for arm in cfg.arms:
        importance = importance_for(arm, cfg.n_features)
        for s_idx, sparsity in enumerate(cfg.sparsities):
            baseline = dedicated_loss(importance, sparsity, cfg.n_dims)
            ratio = 1.0 if s_idx == 0 else (sparse_ratio if s_idx == len(cfg.sparsities) - 1 else 0.8)
            for seed in cfg.seeds:
                loss = baseline * ratio
                trajectory = [(0, baseline), (90, loss), (100, loss)]
                if bad_cell and arm == "uniform" and sparsity == 0.9 and seed >= 3:
                    trajectory = [(0, baseline), (90, loss), (100, loss + 0.1 * baseline)]
                cells[f"{arm}|{sparsity:.3f}|{seed}"] = {
                    "arm": arm,
                    "sparsity": sparsity,
                    "seed": seed,
                    "weight": _weight(
                        cfg,
                        counts[s_idx],
                        extra_norm=extra_norm,
                        wrong_order=wrong_order and arm == "importance" and s_idx == 0,
                    ),
                    "bias": [0.0] * cfg.n_features,
                    "trajectory": trajectory,
                    "final_loss": loss,
                }
    return {"schema_version": 1, "config": config_dict(cfg), "cells": cells}, cfg


def _info(**kwargs):
    cache, cfg = synth_cache(**kwargs)
    return decide(analyze(cache, cfg), cfg)


def test_verdict_superposition_emerges():
    info = _info()
    assert info["status"] == "pass"
    assert info["verdict"] == "superposition_emerges_with_sparsity"
    assert all(info["gates"][key] for key in ("g1_convergence", "g2_emergence", "g3_monotone", "g4_optimality"))
    assert info["gates"]["g5_importance_order"] is True


def test_verdict_dedicated_null():
    info = _info(counts=[1, 2, 3, 4, 5], sparse_ratio=1.0)
    assert info["status"] == "pass"
    assert info["verdict"] == "no_superposition_dedicated_only"
    assert info["gates"]["dedicated_null"] is True


def test_verdict_not_optimal():
    info = _info(sparse_ratio=1.0)
    assert info["status"] == "pass"
    assert info["verdict"] == "superposition_not_optimal"
    assert info["gates"]["g2_emergence"] is True
    assert info["gates"]["g4_optimality"] is False


def test_mixed_tau_routes_review():
    info = _info(extra_norm=0.5)
    assert info["status"] == "review"
    assert info["verdict"] == "review"
    assert info["gates"]["mixed_tau"] is True


def test_nonmonotone_routes_review():
    info = _info(counts=[5, 9, 6, 10, 12])
    assert info["status"] == "review"
    assert info["gates"]["g3_monotone"] is False


def test_unconverged_cell_routes_review():
    info = _info(bad_cell=True)
    assert info["status"] == "review"
    assert info["gates"]["g1_convergence"] is False
    assert info["kept_counts"]["uniform|0.900"] == 3


def test_g5_is_separate_from_headline():
    info = _info(wrong_order=True)
    assert info["verdict"] == "superposition_emerges_with_sparsity"
    assert info["gates"]["g5_importance_order"] is False


def test_probe_gate_requires_both_arms():
    cache, cfg = synth_cache()
    keys = {f"{arm}|{s:.3f}|0" for arm in cfg.arms for s in (0.0, 0.99)}
    probe = {"schema_version": 1, "config": config_dict(cfg), "cells": {key: cache["cells"][key] for key in keys}}
    assert probe_ready(probe, cfg) is True
    probe["cells"]["uniform|0.990|0"]["weight"] = _weight(cfg, 5)
    assert probe_ready(probe, cfg) is False


def test_phase_a_smoke_and_resume():
    cfg = SuperConfig(
        n_features=6,
        n_dims=2,
        sparsities=(0.0, 0.99),
        arms=("importance", "uniform"),
        seeds=(0,),
        steps=20,
        batch_size=32,
        rec_every=10,
        traj_eval_size=32,
        final_eval_size=64,
        min_kept=1,
    )
    torch.set_num_threads(1)
    probe = run_phase_a(cfg, cells=probe_cells(cfg))
    assert len(probe["cells"]) == 4
    resumed = run_phase_a(cfg, prior=probe)
    assert probe["cells"] == resumed["cells"]
    result = analyze(resumed, cfg)
    assert len(result["rows"]) == 4
    assert all(len(row["norms"]) == 6 for row in result["rows"])


def test_cache_verdict_is_byte_stable():
    cache, cfg = synth_cache()
    result = analyze(cache, cfg)
    assert decide(result, cfg) == decide(result, cfg)


def test_report_shape_and_scope():
    cache, cfg = synth_cache()
    result = analyze(cache, cfg)
    info = decide(result, cfg)
    report = build_report(result, info, "cache.pt", generated_at="fixed")
    assert report["status"] == "pass"
    assert report["summary"]["scope"] == "toy_autoencoder_own_substrate"
    assert len(report["rows"]) == 50
    assert all(set(report["csv_fieldnames"]) == set(row) for row in report["rows"])


def test_actual_cache_rederives_verdict():
    root = Path(__file__).resolve().parents[1]
    paths = list((root / "f" / "1276").rglob("phase_a_cache.pt"))
    if not paths:
        pytest.skip("v1276 Phase-A cache is created only after the preregistration commit")
    assert len(paths) == 1
    cache = torch.load(paths[0], map_location="cpu", weights_only=False)
    cfg = SuperConfig()
    result = analyze(cache, cfg)
    first = decide(result, cfg)
    assert first == decide(analyze(cache, cfg), cfg)
    assert first["verdict"] in {
        "superposition_emerges_with_sparsity",
        "no_superposition_dedicated_only",
        "superposition_not_optimal",
        "review",
    }
