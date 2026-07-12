"""v1276: preregistered toy-model test of feature superposition."""

from __future__ import annotations

import itertools
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median

import torch
import torch.nn as nn
import torch.nn.functional as F

from minigpt.report_utils import utc_now


@dataclass(frozen=True)
class SuperConfig:
    n_features: int = 20
    n_dims: int = 5
    sparsities: tuple[float, ...] = (0.0, 0.7, 0.9, 0.97, 0.99)
    arms: tuple[str, ...] = ("importance", "uniform")
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4)
    steps: int = 6000
    batch_size: int = 1024
    lr: float = 0.003
    rec_every: int = 100
    traj_eval_size: int = 8192
    final_eval_size: int = 262144
    taus: tuple[float, ...] = (0.3, 0.5, 0.7)
    plateau_bound: float = 0.02
    min_kept: int = 4
    rho_min: float = 0.9
    p_max: float = 0.05
    optimality_eps: float = 0.02


class ToyAE(nn.Module):
    """Tied ReLU-output autoencoder: x -> ReLU(W^T W x + b)."""

    def __init__(self, n_features: int, n_dims: int) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.empty(n_dims, n_features))
        self.bias = nn.Parameter(torch.zeros(n_features))
        nn.init.xavier_normal_(self.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.relu((x @ self.weight.T) @ self.weight + self.bias)


def config_dict(cfg: SuperConfig) -> dict:
    data = asdict(cfg)
    return {key: list(value) if isinstance(value, tuple) else value for key, value in data.items()}


def importance_for(arm: str, n_features: int) -> torch.Tensor:
    if arm == "importance":
        return torch.tensor([0.7**i for i in range(n_features)], dtype=torch.float32)
    if arm == "uniform":
        return torch.ones(n_features)
    raise ValueError(f"unknown arm: {arm}")


def dedicated_loss(importances, sparsity: float, n_dims: int) -> float:
    """Best dedicated loss: dropped features use the optimal constant E[x]."""
    values = sorted((float(value) for value in importances), reverse=True)
    active_prob = 1.0 - sparsity
    variance = active_prob / 3.0 - active_prob**2 / 4.0
    return variance * sum(values[n_dims:])


def sample_features(n: int, cfg: SuperConfig, sparsity: float, gen: torch.Generator) -> torch.Tensor:
    values = torch.rand((n, cfg.n_features), generator=gen)
    active = torch.rand((n, cfg.n_features), generator=gen) >= sparsity
    return values * active


def weighted_loss(pred: torch.Tensor, target: torch.Tensor, importance: torch.Tensor) -> torch.Tensor:
    return ((pred - target).square() * importance).sum(dim=1).mean()


def cell_key(arm: str, sparsity: float, seed: int) -> str:
    return f"{arm}|{sparsity:.3f}|{seed}"


def all_cells(cfg: SuperConfig) -> list[tuple[str, float, int]]:
    return [(arm, sparsity, seed) for arm in cfg.arms for sparsity in cfg.sparsities for seed in cfg.seeds]


def probe_cells(cfg: SuperConfig) -> list[tuple[str, float, int]]:
    return [(arm, sparsity, cfg.seeds[0]) for arm in cfg.arms for sparsity in (min(cfg.sparsities), max(cfg.sparsities))]


@torch.no_grad()
def _eval_loss(model: ToyAE, x: torch.Tensor, importance: torch.Tensor) -> float:
    model.eval()
    return float(weighted_loss(model(x), x, importance))


def train_cell(cfg: SuperConfig, arm: str, sparsity: float, seed: int) -> dict:
    """Train one CPU cell; RNG is paired across arms for the same (S, seed)."""
    s_idx = cfg.sparsities.index(sparsity)
    torch.manual_seed(1000 + seed)
    model = ToyAE(cfg.n_features, cfg.n_dims)
    importance = importance_for(arm, cfg.n_features)
    train_gen = torch.Generator().manual_seed(2000 + 100 * s_idx + seed)
    traj_gen = torch.Generator().manual_seed(3000 + 100 * s_idx + seed)
    final_gen = torch.Generator().manual_seed(4000 + 100 * s_idx + seed)
    traj_x = sample_features(cfg.traj_eval_size, cfg, sparsity, traj_gen)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    trajectory = []
    for step in range(cfg.steps + 1):
        if step % cfg.rec_every == 0:
            trajectory.append((step, _eval_loss(model, traj_x, importance)))
        if step == cfg.steps:
            break
        x = sample_features(cfg.batch_size, cfg, sparsity, train_gen)
        model.train()
        optimizer.zero_grad(set_to_none=True)
        weighted_loss(model(x), x, importance).backward()
        optimizer.step()
    final_x = sample_features(cfg.final_eval_size, cfg, sparsity, final_gen)
    return {
        "arm": arm, "sparsity": sparsity, "seed": seed,
        "weight": model.weight.detach().tolist(), "bias": model.bias.detach().tolist(),
        "trajectory": trajectory, "final_loss": _eval_loss(model, final_x, importance),
    }


def run_phase_a(
    cfg: SuperConfig,
    *,
    cells: list[tuple[str, float, int]] | None = None,
    prior: dict | None = None,
) -> dict:
    expected = config_dict(cfg)
    if prior is not None and prior.get("config") != expected:
        raise ValueError("resume cache config does not match the preregistered config")
    records = dict((prior or {}).get("cells", {}))
    for arm, sparsity, seed in cells or all_cells(cfg):
        key = cell_key(arm, sparsity, seed)
        if key not in records:
            records[key] = train_cell(cfg, arm, sparsity, seed)
    return {"schema_version": 1, "config": expected, "cells": records}


def tau_key(tau: float) -> str:
    return f"{tau:.1f}"


def weight_metrics(weight, taus: tuple[float, ...]) -> dict:
    tensor = torch.as_tensor(weight, dtype=torch.float32)
    norms = tensor.norm(dim=0)
    directions = tensor / norms.clamp_min(1e-12)
    gram = directions.T @ directions
    gram.fill_diagonal_(0.0)
    interference = gram.square().sum(dim=1)
    return {
        "norms": [round(float(value), 6) for value in norms],
        "interference": [round(float(value), 6) for value in interference],
        "represented": {tau_key(tau): int((norms >= tau).sum()) for tau in taus},
        "represented_sets": {
            tau_key(tau): [idx for idx, value in enumerate(norms) if float(value) >= tau] for tau in taus
        },
    }


def plateau_drift(trajectory, baseline: float, steps: int) -> float:
    tail = [float(loss) for step, loss in trajectory if step >= 0.9 * steps]
    if len(tail) < 2:
        return float("inf")
    return (max(tail) - min(tail)) / max(baseline, 1e-12)


def analyze(cache: dict, cfg: SuperConfig) -> dict:
    if cache.get("config") != config_dict(cfg):
        raise ValueError("cache config does not match the preregistered config")
    rows = []
    for record in cache.get("cells", {}).values():
        arm = record["arm"]
        sparsity = float(record["sparsity"])
        importance = importance_for(arm, cfg.n_features)
        baseline = dedicated_loss(importance, sparsity, cfg.n_dims)
        metrics = weight_metrics(record["weight"], cfg.taus)
        drift = plateau_drift(record["trajectory"], baseline, cfg.steps)
        rows.append({
            "arm": arm, "sparsity": sparsity, "seed": int(record["seed"]),
            "final_loss": float(record["final_loss"]), "dedicated_loss": baseline,
            "loss_ratio": float(record["final_loss"]) / max(baseline, 1e-12),
            "plateau_drift": drift, "converged": drift <= cfg.plateau_bound,
            "mean_interference": sum(metrics["interference"]) / len(metrics["interference"]),
            **metrics,
        })
    rows.sort(key=lambda row: (row["arm"], row["sparsity"], row["seed"]))
    return {"config": config_dict(cfg), "rows": rows}


def _ranks(values) -> list[float]:
    order = sorted(range(len(values)), key=lambda idx: values[idx])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2.0
        for pos in range(start, end):
            ranks[order[pos]] = rank
        start = end
    return ranks


def _corr(left, right) -> float:
    l_mean = sum(left) / len(left)
    r_mean = sum(right) / len(right)
    numerator = sum((a - l_mean) * (b - r_mean) for a, b in zip(left, right))
    denominator = math.sqrt(sum((a - l_mean) ** 2 for a in left) * sum((b - r_mean) ** 2 for b in right))
    return numerator / denominator if denominator else 0.0


def spearman_exact(values) -> tuple[float, float]:
    x_ranks = _ranks(list(range(len(values))))
    observed = _corr(x_ranks, _ranks(values))
    permutations = list(itertools.permutations(values))
    extreme = sum(_corr(x_ranks, _ranks(list(candidate))) >= observed - 1e-12 for candidate in permutations)
    return observed, extreme / len(permutations)


def _cell_rows(result: dict, arm: str, sparsity: float, *, kept: bool = True) -> list[dict]:
    rows = [row for row in result["rows"] if row["arm"] == arm and row["sparsity"] == sparsity]
    return [row for row in rows if row["converged"]] if kept else rows


def decide(result: dict, cfg: SuperConfig) -> dict:
    expected = len(cfg.arms) * len(cfg.sparsities) * len(cfg.seeds)
    raw_complete = len(result.get("rows", [])) == expected
    kept_counts = {}
    for arm in cfg.arms:
        for sparsity in cfg.sparsities:
            kept_counts[f"{arm}|{sparsity:.3f}"] = len(_cell_rows(result, arm, sparsity))
    g1 = raw_complete and all(count >= cfg.min_kept for count in kept_counts.values())

    dense, sparse = min(cfg.sparsities), max(cfg.sparsities)
    g2_checks = {}
    null_checks = {}
    for arm in cfg.arms:
        for tau in cfg.taus:
            key = f"{arm}|{tau_key(tau)}"
            dense_rows = _cell_rows(result, arm, dense)
            sparse_rows = _cell_rows(result, arm, sparse)
            dense_ok = sum(row["represented"][tau_key(tau)] <= cfg.n_dims for row in dense_rows) >= cfg.min_kept
            sparse_ok = sum(row["represented"][tau_key(tau)] > cfg.n_dims for row in sparse_rows) >= cfg.min_kept
            g2_checks[key] = dense_ok and sparse_ok
            null_checks[key] = dense_ok and sum(
                row["represented"][tau_key(tau)] <= cfg.n_dims for row in sparse_rows
            ) >= cfg.min_kept
    g2 = all(g2_checks.values())
    dedicated_null = all(null_checks.values())
    mixed_tau = not g2 and not dedicated_null

    trends = {}
    for arm in cfg.arms:
        medians = []
        for sparsity in cfg.sparsities:
            values = [row["represented"]["0.5"] for row in _cell_rows(result, arm, sparsity)]
            medians.append(median(values) if values else 0.0)
        rho, p_value = spearman_exact(medians)
        nondecreasing = all(left <= right for left, right in zip(medians, medians[1:]))
        trends[arm] = {"medians": medians, "rho": rho, "p_value": p_value, "nondecreasing": nondecreasing}
    g3 = all(v["nondecreasing"] and v["rho"] >= cfg.rho_min and v["p_value"] <= cfg.p_max for v in trends.values())

    optimality = {}
    for arm in cfg.arms:
        dense_rows = _cell_rows(result, arm, dense)
        sparse_rows = _cell_rows(result, arm, sparse)
        dense_loss = median(row["final_loss"] for row in dense_rows) if dense_rows else float("inf")
        sparse_loss = median(row["final_loss"] for row in sparse_rows) if sparse_rows else float("inf")
        dense_base = dedicated_loss(importance_for(arm, cfg.n_features), dense, cfg.n_dims)
        sparse_base = dedicated_loss(importance_for(arm, cfg.n_features), sparse, cfg.n_dims)
        optimality[arm] = {
            "dense_not_better": dense_loss >= dense_base * (1.0 - cfg.optimality_eps),
            "sparse_better": sparse_loss <= sparse_base * (1.0 - cfg.optimality_eps),
            "dense_loss": dense_loss, "dense_baseline": dense_base,
            "sparse_loss": sparse_loss, "sparse_baseline": sparse_base,
        }
    g4 = all(row["dense_not_better"] and row["sparse_better"] for row in optimality.values())

    top_m = set(range(cfg.n_dims))
    importance_dense = _cell_rows(result, "importance", dense)
    g5_count = sum(set(row["represented_sets"]["0.5"]) == top_m for row in importance_dense)
    g5 = g5_count >= cfg.min_kept
    if not g1 or not g3 or mixed_tau:
        verdict = "review"
    elif dedicated_null:
        verdict = "no_superposition_dedicated_only"
    elif g2 and not g4:
        verdict = "superposition_not_optimal"
    elif g2 and g4:
        verdict = "superposition_emerges_with_sparsity"
    else:
        verdict = "review"
    return {
        "status": "review" if verdict == "review" else "pass", "verdict": verdict,
        "gates": {"g1_convergence": g1, "g2_emergence": g2, "g3_monotone": g3,
                  "g4_optimality": g4, "g5_importance_order": g5, "mixed_tau": mixed_tau,
                  "dedicated_null": dedicated_null, "raw_complete": raw_complete},
        "kept_counts": kept_counts, "g2_checks": g2_checks, "trends": trends,
        "optimality": optimality, "g5_match_count": g5_count,
    }


def probe_ready(cache: dict, cfg: SuperConfig) -> bool:
    if cache.get("config") != config_dict(cfg):
        return False
    sparse = max(cfg.sparsities)
    for arm in cfg.arms:
        record = cache.get("cells", {}).get(cell_key(arm, sparse, cfg.seeds[0]))
        if record is None or weight_metrics(record["weight"], cfg.taus)["represented"]["0.3"] <= cfg.n_dims:
            return False
    return all(cell_key(*cell) in cache.get("cells", {}) for cell in probe_cells(cfg))


def build_report(result: dict, info: dict, source: str, generated_at: str | None = None) -> dict:
    rows = []
    for row in result["rows"]:
        rows.append({
            "arm": row["arm"], "sparsity": row["sparsity"], "seed": row["seed"],
            "converged": row["converged"], "final_loss": round(row["final_loss"], 8),
            "dedicated_loss": round(row["dedicated_loss"], 8), "loss_ratio": round(row["loss_ratio"], 6),
            "r_0_3": row["represented"]["0.3"], "r_0_5": row["represented"]["0.5"],
            "r_0_7": row["represented"]["0.7"], "mean_interference": round(row["mean_interference"], 6),
        })
    summary = {
        "verdict": info["verdict"], "scope": "toy_autoencoder_own_substrate", "source_cache": source,
        **info["gates"], "g5_match_count": info["g5_match_count"],
        "importance_rho": round(info["trends"]["importance"]["rho"], 6),
        "uniform_rho": round(info["trends"]["uniform"]["rho"], 6),
        "importance_sparse_loss_ratio": round(info["optimality"]["importance"]["sparse_loss"] / info["optimality"]["importance"]["sparse_baseline"], 6),
        "uniform_sparse_loss_ratio": round(info["optimality"]["uniform"]["sparse_loss"] / info["optimality"]["uniform"]["sparse_baseline"], 6),
    }
    return {
        "schema_version": 1, "title": "MiniGPT v1276 toy-model superposition",
        "description": "Preregistered CPU test of whether sparse features are loss-optimally packed into too few dimensions.",
        "generated_at": generated_at or utc_now(), "status": info["status"], "decision": info["verdict"],
        "summary": summary, "rows": rows,
        "recommendations": [
            "Interpret the verdict only for the 20-feature, 5-dimension toy autoencoder.",
            "Re-derive thresholds from the committed cache; do not retrain during Phase B.",
            "Treat the importance-order gate separately from the superposition headline.",
        ],
        "csv_fieldnames": list(rows[0]) if rows else [],
    }


def plot_result(result: dict, info: dict, path: str | Path) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, len(result["config"]["arms"]), figsize=(11, 4.8), sharey=True)
    for axis, arm in zip(axes, result["config"]["arms"]):
        for tau in result["config"]["taus"]:
            values = [median(row["represented"][tau_key(tau)] for row in _cell_rows(result, arm, s)) for s in result["config"]["sparsities"]]
            axis.plot(result["config"]["sparsities"], values, marker="o", label=f"tau={tau}")
        axis.axhline(result["config"]["n_dims"], color="black", linestyle="--", label="m=5")
        axis.set(title=arm, xlabel="Feature sparsity S", ylabel="Represented feature count")
        axis.legend()
    fig.suptitle(f"v1276 superposition: {info['verdict']}")
    fig.tight_layout()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)


__all__ = [
    "SuperConfig", "ToyAE", "all_cells", "analyze", "build_report", "cell_key", "config_dict",
    "decide", "dedicated_loss", "importance_for", "plot_result", "probe_cells", "probe_ready",
    "run_phase_a", "sample_features", "spearman_exact", "train_cell", "weight_metrics", "weighted_loss",
]
