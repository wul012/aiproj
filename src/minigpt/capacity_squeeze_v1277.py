"""v1277: capacity squeeze -- drop frequencies, superpose them, or fail?

Squeezes the grokked transformer's ``n_embd`` below the Fourier circuit's
orthogonal footprint (P1: k_func=4 frequencies -> 8 dimensions) and classifies,
per trained cell, whether the model keeps more frequencies than fit orthogonally
(``forced_packing``), economizes to a set that fits (``economized``), groks some
non-Fourier way (``off_mechanism``), or fails to grok. Phase A trains the width
grid once and caches per-cell metrics; Phase B re-derives the verdict CPU-only.

Preregistered before any Phase-A run (see docs/v1277-capacity-squeeze-brief.md).
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

from minigpt.grok_checkpoint_v1185 import train_to_grok
from minigpt.grok_freq_ablation_v1191 import ablated_model
from minigpt.grok_interp_v1188 import embedding_spectrum, number_embedding
from minigpt.grok_predict_v1186 import evaluate_table
from minigpt.grok_v1179 import GrokConfig
from minigpt.report_utils import utc_now

VERDICTS = (
    "squeeze_forces_superposition",
    "squeeze_drops_features",
    "squeeze_hits_capacity_floor",
    "review",
)


@dataclass(frozen=True)
class SqueezeConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    max_steps: int = 40000
    n_head: int = 4
    widths: tuple[int, ...] = (32, 16, 12, 8, 4)
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    grok_bar: float = 0.90
    keep_ratio: float = 0.90
    keep_ratio_grid: tuple[float, ...] = (0.85, 0.90, 0.95)
    k_max: int = 8
    squeeze_widths: tuple[int, ...] = (8, 4)
    baseline_width: int = 32
    min_grokked_squeeze: int = 2
    dominance: float = 0.70
    off_mech_bar: float = 0.30
    gram_ortho_bar: float = 0.30
    max_runs: int = 20
    # P1 calibration facts, recorded for the report (not gates):
    p1_k_func: int = 4
    p1_gram_maxcos: float = 0.066
    p1_n_eff: float = 27.3

    def validate(self) -> None:
        if any(w % self.n_head != 0 for w in self.widths):
            raise ValueError("every width must be divisible by n_head")
        if not set(self.squeeze_widths) <= set(self.widths):
            raise ValueError("squeeze_widths must be a subset of widths")
        if self.baseline_width not in self.widths:
            raise ValueError("baseline_width must be in widths")
        if len(self.widths) * len(self.seeds) + 1 > self.max_runs:
            raise ValueError("width x seed grid exceeds the GPU run budget")
        if self.keep_ratio not in self.keep_ratio_grid:
            raise ValueError("keep_ratio must be on the robustness grid")


# ---------------------------------------------------------------- metrics ----
def participation_ratio(power: torch.Tensor) -> float:
    """(sum p)^2 / sum p^2 -- effective count of a nonnegative vector."""
    total = float(power.sum())
    if total <= 0:
        return 0.0
    return float(total * total / float((power * power).sum()))


def feature_directions(E: torch.Tensor, freqs: list[int], p: int) -> torch.Tensor:
    """Unit-norm images of the cos/sin waves of ``freqs`` under ``E.T``: (2k, d)."""
    ks = torch.arange(p, dtype=torch.float32)
    dirs = []
    for f in freqs:
        for wave in (torch.cos, torch.sin):
            u = wave(2 * torch.pi * float(f) * ks / p)
            v = E.T.float() @ u
            norm = float(v.norm())
            dirs.append(v / norm if norm > 0 else v)
    return torch.stack(dirs)


def gram_offdiag(dirs: torch.Tensor) -> dict:
    """Max |cos| and mean-square of the off-diagonal Gram entries."""
    gram = (dirs @ dirs.T).abs()
    n = gram.shape[0]
    off = gram - torch.diag(torch.diag(gram))
    denom = n * n - n
    return {
        "maxcos": round(float(off.max()), 6),
        "meansq": round(float((off * off).sum() / denom), 6) if denom else 0.0,
    }


def top_freqs(power: torch.Tensor, k: int) -> list[int]:
    """Top-k folded frequencies (1-indexed) of a non-DC power vector."""
    idx = torch.argsort(power, descending=True)
    return [int(i.item()) + 1 for i in idx[:k]]


def k_func_of(keep_accs: list[float], heldout: float, ratio: float) -> int | None:
    """Min k (1-indexed) whose keep-top-k accuracy reaches ratio*heldout."""
    bar = ratio * heldout
    for i, acc in enumerate(keep_accs):
        if acc >= bar:
            return i + 1
    return None


def cell_metrics(model, meta, cfg: SqueezeConfig) -> dict:
    """All Phase-B inputs for one trained cell (model is discarded afterwards)."""
    heldout = evaluate_table(model, meta)["heldout_acc"]
    E = number_embedding(model, cfg.p)
    power = embedding_spectrum(E)
    freqs8 = top_freqs(power, cfg.k_max)
    keep_accs = []
    gram_by_k = {}
    for k in range(1, cfg.k_max + 1):
        freqs = freqs8[:k]
        keep = ablated_model(model, cfg.p, freqs, "keep")
        keep_accs.append(round(evaluate_table(keep, meta)["heldout_acc"], 6))
        gram_by_k[k] = gram_offdiag(feature_directions(E, freqs, cfg.p))
    return {
        "width": meta.n_embd,
        "seed": meta.seed,
        "steps_run": meta.steps_run,
        "t_mem": meta.t_mem,
        "t_gen": meta.t_gen,
        "final_train_acc": round(meta.final_train_acc, 6),
        "final_val_acc": round(meta.final_val_acc, 6),
        "heldout_acc": round(heldout, 6),
        "power": [round(float(x), 8) for x in power],
        "top_freqs": freqs8,
        "keep_accs": keep_accs,
        "gram_by_k": gram_by_k,
        "n_eff": round(participation_ratio(power), 4),
    }


# ---------------------------------------------------------------- phase A ----
def train_cell(cfg: SqueezeConfig, width: int, seed: int, device) -> tuple:
    """One canonical-recipe run with n_embd overridden to ``width``."""
    grok_cfg = GrokConfig(
        p=cfg.p, train_frac=cfg.train_frac, n_head=cfg.n_head, n_embd=width,
        max_steps=cfg.max_steps, seeds=(seed,), wds=(cfg.weight_decay,),
    )
    return train_to_grok(grok_cfg, device)


def run_phase_a(cfg: SqueezeConfig, device, trainer=train_cell, metrics=cell_metrics) -> dict:
    """Train the full grid once; return the cache dict (small, model-free)."""
    cfg.validate()
    cells = []
    for width in cfg.widths:
        for seed in cfg.seeds:
            model, meta, _curve = trainer(cfg, width, seed, device)
            cells.append(metrics(model, meta, cfg))
            del model
    return {"schema": "capacity_squeeze_v1277.v1", "generated_at": utc_now(),
            "config": cfg.__dict__ | {"widths": list(cfg.widths), "seeds": list(cfg.seeds),
                                      "keep_ratio_grid": list(cfg.keep_ratio_grid),
                                      "squeeze_widths": list(cfg.squeeze_widths)},
            "cells": cells}


# ---------------------------------------------------------------- phase B ----
def classify_cell(cell: dict, cfg: SqueezeConfig, ratio: float) -> str:
    if cell["heldout_acc"] < cfg.grok_bar:
        return "not_grokked"
    k = k_func_of(cell["keep_accs"], cell["heldout_acc"], ratio)
    if k is None:
        return "off_mechanism"
    return "forced_packing" if 2 * k > cell["width"] else "economized"


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return float("nan")
    mid = n // 2
    return float(ordered[mid]) if n % 2 else float((ordered[mid - 1] + ordered[mid]) / 2)


def _verdict_at_ratio(cells: list[dict], cfg: SqueezeConfig, ratio: float) -> dict:
    squeeze = [c for c in cells if c["width"] in cfg.squeeze_widths]
    grokked = [c for c in squeeze if c["heldout_acc"] >= cfg.grok_bar]
    classes = [classify_cell(c, cfg, ratio) for c in grokked]
    n = len(grokked)
    counts = {name: classes.count(name) for name in
              ("forced_packing", "economized", "off_mechanism")}
    if n < cfg.min_grokked_squeeze:
        verdict = "squeeze_hits_capacity_floor"
    elif counts["off_mechanism"] >= cfg.off_mech_bar * n:
        verdict = "review"
    elif counts["forced_packing"] >= cfg.dominance * n:
        verdict = "squeeze_forces_superposition"
    elif counts["economized"] >= cfg.dominance * n:
        verdict = "squeeze_drops_features"
    else:
        verdict = "review"
    return {"ratio": ratio, "verdict": verdict, "grokked_squeeze_cells": n,
            "class_counts": counts}


def decide(cache: dict, cfg: SqueezeConfig | None = None) -> dict:
    """Preregistered gates + ladder; pure function of the Phase-A cache."""
    cfg = cfg or SqueezeConfig()
    cells = cache["cells"]
    base = [c for c in cells if c["width"] == cfg.baseline_width]
    base_grokked = [c for c in base if c["heldout_acc"] >= cfg.grok_bar]
    base_k = [k for c in base_grokked
              if (k := k_func_of(c["keep_accs"], c["heldout_acc"], cfg.keep_ratio))]
    base_gram = [c["gram_by_k"][k]["maxcos"] for c, k in zip(base_grokked, base_k)]
    g0 = (len(base_grokked) >= 2 and len(base_k) == len(base_grokked)
          and 2 <= _median([float(k) for k in base_k]) <= cfg.k_max
          and _median(base_gram) <= cfg.gram_ortho_bar)
    expected = len(cfg.widths) * len(cfg.seeds)
    g1 = len(cells) == expected
    ladder = [_verdict_at_ratio(cells, cfg, r) for r in cfg.keep_ratio_grid]
    at_main = next(e for e in ladder if e["ratio"] == cfg.keep_ratio)
    g2 = len({e["verdict"] for e in ladder}) == 1
    if not g0:
        verdict, reason = "review", "substrate_unsound"
    elif not g1:
        verdict, reason = "review", "grid_incomplete"
    elif not g2:
        verdict, reason = "review", "ratio_unstable"
    else:
        verdict, reason = at_main["verdict"], at_main["verdict"]
    smallest = min((c["width"] for c in cells if c["heldout_acc"] >= cfg.grok_bar),
                   default=None)
    return {
        "status": "pass",
        "verdict": verdict,
        "reason": reason,
        "g0_substrate": g0,
        "g1_complete": g1,
        "g2_ratio_stable": g2,
        "baseline_k_func": [int(k) for k in base_k],
        "baseline_gram_maxcos": base_gram,
        "ladder": ladder,
        "main": at_main,
        "smallest_grokking_width": smallest,
        "scope": "own_grokked_substrate_toy_scale",
    }


# ----------------------------------------------------------------- report ----
def build_report(cache: dict, info: dict, generated_at: str | None = None) -> dict:
    cfg = SqueezeConfig()
    rows = []
    for c in cache["cells"]:
        k = k_func_of(c["keep_accs"], c["heldout_acc"], cfg.keep_ratio)
        gram = c["gram_by_k"][k]["maxcos"] if k else None
        rows.append({
            "width": c["width"], "seed": c["seed"], "heldout_acc": c["heldout_acc"],
            "t_gen": c["t_gen"], "k_func": k, "footprint": 2 * k if k else None,
            "gram_maxcos_at_k": gram, "n_eff": c["n_eff"],
            "class": classify_cell(c, cfg, cfg.keep_ratio),
        })
    main = info["main"]
    flat = {
        "verdict": info["verdict"],
        "reason": info["reason"],
        "scope": info["scope"],
        "g0_substrate": info["g0_substrate"],
        "g1_complete": info["g1_complete"],
        "g2_ratio_stable": info["g2_ratio_stable"],
        "keep_ratio": cfg.keep_ratio,
        "grokked_squeeze_cells": main["grokked_squeeze_cells"],
        "forced_packing": main["class_counts"]["forced_packing"],
        "economized": main["class_counts"]["economized"],
        "off_mechanism": main["class_counts"]["off_mechanism"],
        "smallest_grokking_width": info["smallest_grokking_width"],
        "baseline_k_func_median": _median([float(k) for k in info["baseline_k_func"]]),
        "baseline_gram_median": _median(info["baseline_gram_maxcos"]),
    }
    return {
        "schema_version": 1,
        "title": "MiniGPT v1277 capacity squeeze",
        "description": "Preregistered width squeeze of the grokked Fourier circuit: "
                       "drop frequencies, superpose them, or fail.",
        "generated_at": generated_at or utc_now(),
        "status": info["status"],
        "decision": info["verdict"],
        "summary": flat,
        "ladder": info["ladder"],
        "cells": rows,
        "artifacts": [],
        "recommendations": _recommendations(info),
        "warnings": [],
    }


def _recommendations(info: dict) -> list[str]:
    v = info["verdict"]
    if v == "squeeze_forces_superposition":
        return ["Measure whether packed cells trade accuracy margin for interference.",
                "Candidate follow-up: activation-space superposition probe on MiniGPT."]
    if v == "squeeze_drops_features":
        return ["Map the minimal-frequency frontier: k_func versus width curve.",
                "Check whether dropped cells grok slower (t_gen versus width)."]
    if v == "squeeze_hits_capacity_floor":
        return ["Locate the floor: sweep between the smallest grokking width and the "
                "largest failing width with a longer step budget."]
    return ["Adjudicate the review branch externally before any follow-up."]


def plot_result(cache: dict, info: dict, path) -> None:
    """One figure: k_func and top-k interference versus width, with the
    orthogonal-footprint boundary k = w/2 marked."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path as _Path

    cfg = SqueezeConfig()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
    widths = sorted({c["width"] for c in cache["cells"]})
    for c in cache["cells"]:
        grokked = c["heldout_acc"] >= cfg.grok_bar
        k = k_func_of(c["keep_accs"], c["heldout_acc"], cfg.keep_ratio) if grokked else None
        if k is not None:
            forced = 2 * k > c["width"]
            ax1.scatter(c["width"], k, marker="o" if forced else "s",
                        color="tab:red" if forced else "tab:blue", zorder=3)
            ax2.scatter(c["width"], c["gram_by_k"][k]["maxcos"], marker="o",
                        color="tab:red" if forced else "tab:blue", zorder=3)
        else:
            ax1.scatter(c["width"], 0, marker="x", color="gray", zorder=3)
    boundary = [w / 2 for w in widths]
    ax1.plot(widths, boundary, "k--", label="orthogonal footprint k = w/2")
    ax1.axhline(cfg.p1_k_func, color="green", linestyle=":", label="baseline k_func=4")
    ax1.set(xlabel="n_embd (width)", ylabel="k_func (min sufficient frequencies)",
            title="functional frequency count vs width")
    ax1.legend(fontsize=8)
    ax2.axhline(cfg.gram_ortho_bar, color="green", linestyle=":", label="ortho bar 0.30")
    ax2.set(xlabel="n_embd (width)", ylabel="max |cos| among top-k directions",
            title="feature interference vs width")
    ax2.legend(fontsize=8)
    fig.suptitle(f"v1277 capacity squeeze: {info['verdict']}")
    fig.tight_layout()
    out = _Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)


def summarize(report: dict) -> list[str]:
    lines = [f"status={report['status']}", f"decision={report['decision']}"]
    lines += [f"{key}={value}" for key, value in report["summary"].items()]
    for entry in report["ladder"]:
        counts = entry["class_counts"]
        lines.append(
            f"ratio={entry['ratio']}: verdict={entry['verdict']} "
            f"grokked={entry['grokked_squeeze_cells']} forced={counts['forced_packing']} "
            f"econ={counts['economized']} offmech={counts['off_mechanism']}"
        )
    for row in report["cells"]:
        lines.append(
            f"w={row['width']} seed={row['seed']}: acc={row['heldout_acc']} "
            f"k_func={row['k_func']} class={row['class']} gram={row['gram_maxcos_at_k']}"
        )
    return lines
