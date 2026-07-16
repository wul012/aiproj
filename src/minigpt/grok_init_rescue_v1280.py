"""v1280: is small-init grokking death an lr artifact?

v1279 found that shrinking d=128's init norm (alpha <= 0.5) prevents grokking;
the v1280 P1 probe corrected the interpretation: those cells memorize instantly
(t_mem 200-300) and then sit fully memorized forever -- the death is of the
memorize->generalize transition. Under AdamW the relative update is lr/|w|,
so the frozen lr=1e-3 at alpha=0.5 is ~2x the baseline's relative step. This
version sweeps lr at alpha=0.5 in both directions (the rescue arm) and alpha
between 0.5 and 1 (the dose arm), against the committed v1279 cache as the
read-only reference.

Preregistered before any GPU run (see docs/v1280-init-rescue-brief.md).
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from minigpt.grok_checkpoint_v1185 import train_to_grok
from minigpt.grok_predict_v1186 import evaluate_table
from minigpt.grok_speed_v1279 import scaled_init, t_gen_at, total_norm_of
from minigpt.grok_v1179 import GrokConfig

SCHEMA = "grok_init_rescue_v1280.v1"
VERDICTS = (
    "stuck_memorized_robust_to_lr",
    "norm_clock_revived_under_lr_scaling",
    "lr_rescues_grokking_without_speedup",
    "review",
)
CELL_CLASSES = ("grokked", "stuck_memorized", "broken")


@dataclass(frozen=True)
class RescueConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    width: int = 128
    # one clock for all new cells: > 5x the reference baseline median t_gen
    # (11,400) and > the worst observed grokking cell (35,000 at d=64).
    max_steps: int = 60000
    alpha_dead: float = 0.5
    base_lr: float = 1e-3
    rescue_lrs: tuple[float, ...] = (2.5e-4, 5e-4, 2e-3, 4e-3)
    dose_alphas: tuple[float, ...] = (0.6, 0.7, 0.85)
    seeds: tuple[int, ...] = (1337, 1338)
    confirm_seed: int = 1339
    grok_bar: float = 0.90
    heldout_bar: float = 0.90
    mem_bar: float = 0.99
    tgen_bars: tuple[float, ...] = (0.85, 0.90, 0.95)
    # G0 integrity anchor: the reference cache's alpha=1 median t_gen at bar 0.90
    baseline_median_tgen: float = 11400.0
    max_runs: int = 18

    def validate(self) -> None:
        if self.base_lr in self.rescue_lrs:
            raise ValueError("rescue lrs must differ from the frozen base lr")
        if any(lr <= 0 for lr in self.rescue_lrs):
            raise ValueError("rescue lrs must be positive")
        if not all(self.alpha_dead < a < 1.0 for a in self.dose_alphas):
            raise ValueError("dose alphas must lie strictly between alpha_dead and 1")
        if self.confirm_seed in self.seeds:
            raise ValueError("confirm seed must be fresh")
        if self.grok_bar not in self.tgen_bars:
            raise ValueError("grok_bar must be on the robustness grid")
        if self.planned_min() + len(self.rescue_lrs) > self.max_runs:
            raise ValueError("worst-case confirms exceed the GPU budget")

    def planned_min(self) -> int:
        return (len(self.rescue_lrs) + len(self.dose_alphas)) * len(self.seeds)


# ------------------------------------------------------------ cell classes ----
def t_mem_at(curve: list[tuple[int, float, float]], bar: float) -> int | None:
    """First eval step whose TRAIN accuracy reaches bar; None = never memorized."""
    for step, train_acc, _val_acc in curve:
        if train_acc >= bar:
            return step
    return None


def _val_pairs(cell: dict) -> list[tuple[int, float]]:
    rows = [tuple(r) for r in cell["curve"]]
    return [(r[0], r[-1]) for r in rows]  # v1280 rows (step,train,val); refs (step,val)


def cell_tgen(cell: dict, bar: float) -> float:
    t = t_gen_at(_val_pairs(cell), bar)
    return math.inf if t is None else float(t)


def classify(cell: dict, bar: float, cfg: RescueConfig) -> str:
    """grokked / stuck_memorized / broken, from the cached curves and heldout."""
    if math.isfinite(cell_tgen(cell, bar)) and cell["heldout_acc"] >= cfg.heldout_bar:
        return "grokked"
    rows = [tuple(r) for r in cell["curve"]]
    if len(rows[0]) == 3:
        t_mem = t_mem_at(rows, cfg.mem_bar)
    else:  # v1279 reference cells cache only the val curve; t_mem is a field
        t_mem = cell["t_mem"]
    return "stuck_memorized" if t_mem is not None else "broken"


# ---------------------------------------------------------------- phase A ----
def train_cell(cfg: RescueConfig, alpha: float, lr: float, seed: int, device) -> dict:
    init = scaled_init(cfg.width, seed, alpha, cfg)
    grok_cfg = GrokConfig(p=cfg.p, train_frac=cfg.train_frac, n_head=cfg.n_head,
                          n_embd=cfg.width, max_steps=cfg.max_steps, lr=lr,
                          seeds=(seed,), wds=(cfg.weight_decay,))
    model, meta, curve = train_to_grok(grok_cfg, device, init_state=init)
    heldout = evaluate_table(model, meta)["heldout_acc"]
    both_curves = [(int(r["step"]), float(r["train_acc"]), float(r["val_acc"]))
                   for r in curve]
    return {
        "alpha": alpha, "lr": lr, "seed": seed,
        "n0": round(total_norm_of(init), 4),
        "t_mem": meta.t_mem, "t_gen": meta.t_gen, "steps_run": meta.steps_run,
        "final_train_acc": round(meta.final_train_acc, 6),
        "final_val_acc": round(meta.final_val_acc, 6),
        "heldout_acc": round(heldout, 6),
        "curve": both_curves,
    }


def _confirm_lrs(cells: list[dict], cfg: RescueConfig) -> list[float]:
    """Deterministic rule: an lr with exactly one grokked seed gets a confirm."""
    out = []
    for lr in sorted(cfg.rescue_lrs):
        seed_cells = [c for c in cells if c["arm"] == "rescue" and c["lr"] == lr]
        if sum(classify(c, cfg.grok_bar, cfg) == "grokked" for c in seed_cells) == 1:
            out.append(lr)
    return out


def run_phase_a(cfg: RescueConfig, device, trainer=train_cell) -> dict:
    cfg.validate()
    cells: list[dict] = []
    for lr in cfg.rescue_lrs:
        for seed in cfg.seeds:
            cells.append(trainer(cfg, cfg.alpha_dead, lr, seed, device)
                         | {"arm": "rescue"})
    for lr in _confirm_lrs(cells, cfg):
        if len(cells) + len(cfg.dose_alphas) * len(cfg.seeds) >= cfg.max_runs:
            raise RuntimeError("confirm run would exceed the GPU budget")
        cells.append(trainer(cfg, cfg.alpha_dead, lr, cfg.confirm_seed, device)
                     | {"arm": "rescue_confirm"})
    for alpha in cfg.dose_alphas:
        for seed in cfg.seeds:
            cells.append(trainer(cfg, alpha, cfg.base_lr, seed, device)
                         | {"arm": "dose"})
    return {"schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": asdict(cfg), "cells": cells}


# ----------------------------------------------------------------- decide ----
def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def _reference_arms(reference: dict, cfg: RescueConfig) -> tuple[list, list]:
    base = [c for c in reference["cells"]
            if c["arm"] == "grid" and c["width"] == cfg.width and c["alpha"] == 1.0]
    dead = [c for c in reference["cells"]
            if c["arm"] in ("alpha_wide", "alpha_star") and c["alpha"] < 0.6]
    return base, dead


def _g0_reference(reference: dict, cfg: RescueConfig) -> bool:
    base, dead = _reference_arms(reference, cfg)
    if len(base) != 3 or len(dead) != 6:
        return False
    if any(classify(c, cfg.grok_bar, cfg) != "grokked" for c in base):
        return False
    if _median([cell_tgen(c, cfg.grok_bar) for c in base]) != cfg.baseline_median_tgen:
        return False
    return all(classify(c, cfg.grok_bar, cfg) == "stuck_memorized" for c in dead)


def _g1_complete(cache: dict, cfg: RescueConfig) -> bool:
    cells = cache["cells"]
    rescue = [c for c in cells if c["arm"] == "rescue"]
    confirms = [c for c in cells if c["arm"] == "rescue_confirm"]
    dose = [c for c in cells if c["arm"] == "dose"]
    if len(rescue) != len(cfg.rescue_lrs) * len(cfg.seeds):
        return False
    if len(dose) != len(cfg.dose_alphas) * len(cfg.seeds):
        return False
    return sorted(c["lr"] for c in confirms) == _confirm_lrs(rescue, cfg)


def _rescued_lrs(cells: list[dict], bar: float, cfg: RescueConfig) -> list[float]:
    out = []
    for lr in cfg.rescue_lrs:
        group = [c for c in cells if c["arm"].startswith("rescue") and c["lr"] == lr]
        if sum(classify(c, bar, cfg) == "grokked" for c in group) >= 2:
            out.append(lr)
    return out


def _verdict_at_bar(cache: dict, reference: dict, cfg: RescueConfig, bar: float) -> str:
    base, _ = _reference_arms(reference, cfg)
    base_median = _median([cell_tgen(c, bar) for c in base])
    rescued = _rescued_lrs(cache["cells"], bar, cfg)
    if not rescued:
        return "stuck_memorized_robust_to_lr"
    per_lr = []
    for lr in rescued:
        group = [c for c in cache["cells"]
                 if c["arm"].startswith("rescue") and c["lr"] == lr
                 and classify(c, bar, cfg) == "grokked"]
        per_lr.append(_median([cell_tgen(c, bar) for c in group]))
    best = min(per_lr)  # the best rescue is the statistic (preregistered)
    return ("norm_clock_revived_under_lr_scaling" if best < base_median
            else "lr_rescues_grokking_without_speedup")


def _dose_shape(cache: dict, cfg: RescueConfig) -> str:
    """cliff / graded, descriptive only (preregistered classification)."""
    classes = {}
    for alpha in cfg.dose_alphas:
        group = [c for c in cache["cells"] if c["arm"] == "dose" and c["alpha"] == alpha]
        kinds = {classify(c, cfg.grok_bar, cfg) for c in group}
        if len(kinds) != 1:
            return "graded"
        classes[alpha] = kinds.pop()
    ordered = [classes[a] for a in sorted(classes)]
    collapsed = [k for i, k in enumerate(ordered) if i == 0 or k != ordered[i - 1]]
    return "cliff" if collapsed in (["stuck_memorized", "grokked"],
                                    ["stuck_memorized"], ["grokked"]) else "graded"


def decide(cache: dict, reference: dict, cfg: RescueConfig | None = None) -> dict:
    cfg = cfg or RescueConfig()
    cfg.validate()
    info: dict = {"g0_reference": _g0_reference(reference, cfg),
                  "g1_complete": _g1_complete(cache, cfg)}
    if not info["g0_reference"]:
        return info | {"verdict": "review", "reason": "reference_cache_invalid",
                       "g2_bar_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_bar_stable": False}
    by_bar = {bar: _verdict_at_bar(cache, reference, cfg, bar)
              for bar in cfg.tgen_bars}
    info["verdict_by_bar"] = by_bar
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    rescue_cells = [c for c in cache["cells"] if c["arm"].startswith("rescue")]
    info["rescued_lrs"] = _rescued_lrs(cache["cells"], cfg.grok_bar, cfg)
    info["class_by_lr"] = {
        str(lr): sorted(classify(c, cfg.grok_bar, cfg)
                        for c in rescue_cells if c["lr"] == lr)
        for lr in cfg.rescue_lrs}
    info["dose_shape"] = _dose_shape(cache, cfg)
    if info["g2_bar_stable"]:
        info |= {"verdict": by_bar[cfg.grok_bar], "reason": ""}
    else:
        info |= {"verdict": "review", "reason": "bar_instability"}
    return info


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, reference: dict, info: dict,
                 cfg: RescueConfig | None = None) -> dict:
    cfg = cfg or RescueConfig()
    base, _ = _reference_arms(reference, cfg)
    rows = []
    for c in cache["cells"]:
        t = cell_tgen(c, cfg.grok_bar)
        rows.append({"arm": c["arm"], "alpha": c["alpha"], "lr": c["lr"],
                     "seed": c["seed"],
                     "class": classify(c, cfg.grok_bar, cfg),
                     "t_gen": None if math.isinf(t) else int(t),
                     "t_mem": c["t_mem"], "heldout_acc": c["heldout_acc"]})
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_frozen_recipe_60k_budget",
        "g0_reference": info["g0_reference"], "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "rescued_lrs": info.get("rescued_lrs", []),
        "class_by_lr": info.get("class_by_lr", {}),
        "dose_shape": info.get("dose_shape", ""),
        "baseline_median_tgen": _median([cell_tgen(c, cfg.grok_bar) for c in base]),
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_reference']} g1={s['g1_complete']} g2={s['g2_bar_stable']}",
             f"rescued_lrs={s['rescued_lrs']} dose_shape={s['dose_shape']}"
             f" baseline_median={s['baseline_median_tgen']}"]
    for lr, classes in s["class_by_lr"].items():
        lines.append(f"lr={lr}: {classes}")
    for row in report["cells"]:
        lines.append(f"{row['arm']} a={row['alpha']} lr={row['lr']}"
                     f" seed={row['seed']}: {row['class']} t_gen={row['t_gen']}"
                     f" t_mem={row['t_mem']} heldout={row['heldout_acc']}")
    return lines


def plot_result(cache: dict, reference: dict, info: dict, path) -> None:
    """One figure, two panels: rescue arm lr->t_gen; dose arm alpha->t_gen."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path as _Path

    cfg = RescueConfig()
    base, dead = _reference_arms(reference, cfg)
    base_median = _median([cell_tgen(c, cfg.grok_bar) for c in base])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))

    def y_of(t: float, seen: dict, key) -> float:
        if math.isfinite(t):
            return t
        rank = seen.get(key, 0)
        seen[key] = rank + 1
        return cfg.max_steps * (1.12 + 0.10 * rank)

    seen1: dict = {}
    for c in (x for x in cache["cells"] if x["arm"].startswith("rescue")):
        t = cell_tgen(c, cfg.grok_bar)
        kind = classify(c, cfg.grok_bar, cfg)
        color = {"grokked": "tab:green", "stuck_memorized": "tab:red",
                 "broken": "black"}[kind]
        ax1.scatter(c["lr"], y_of(t, seen1, c["lr"]), color=color, zorder=3)
    ax1.axhline(base_median, color="tab:blue", linestyle="--",
                label=f"alpha=1 baseline median ({int(base_median)})")
    ax1.axhline(cfg.max_steps, color="gray", linestyle=":",
                label="60k budget (censored above)")
    ax1.set(xscale="log", yscale="log", xlabel="lr (log)", ylabel="t_gen (steps, log)",
            title=f"rescue arm: alpha=0.5, lr sweep -> {info['verdict']}")
    ax1.legend(fontsize=7)

    seen2: dict = {}
    for c in (x for x in cache["cells"] if x["arm"] == "dose"):
        t = cell_tgen(c, cfg.grok_bar)
        kind = classify(c, cfg.grok_bar, cfg)
        color = {"grokked": "tab:green", "stuck_memorized": "tab:red",
                 "broken": "black"}[kind]
        ax2.scatter(c["alpha"], y_of(t, seen2, c["alpha"]), color=color, zorder=3)
    for c in base + dead:  # v1279 references, hollow
        t = cell_tgen(c, cfg.grok_bar)
        ax2.scatter(c["alpha"], y_of(t, seen2, ("ref", c["alpha"])),
                    facecolors="none", edgecolors="tab:blue", zorder=2)
    ax2.axhline(cfg.max_steps, color="gray", linestyle=":")
    ax2.set(yscale="log", xlabel="alpha (init scale)", ylabel="t_gen (steps, log)",
            title="dose arm at lr=1e-3 (hollow = v1279 refs): "
                  f"{info.get('dose_shape', '')}")

    fig.tight_layout()
    out = _Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)
