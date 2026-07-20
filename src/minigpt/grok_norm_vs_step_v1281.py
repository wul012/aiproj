"""v1281: norm vs relative step -- what makes v1280's rescued cells fast?

v1280's rescued alpha=0.5 cells differ from the alpha=1 baseline in BOTH init
norm (0.5x) and relative AdamW step (lr/alpha, 4-8x). This version runs the
missing control -- alpha=1 at matched relative step -- against the committed
v1279/v1280 caches as read-only references. Matched pairs:
r=4x: (0.5, 2e-3) ref median 3,900 vs (1, 4e-3) new;
r=8x: (0.5, 4e-3) ref median 1,800 vs (1, 8e-3) new.

Preregistered before any GPU run (see docs/v1281-norm-vs-step-brief.md).
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from minigpt.grok_arc_common import agg_pyplot, median as _median, save_figure
from minigpt.grok_init_rescue_v1280 import cell_tgen, classify, train_cell

SCHEMA = "grok_norm_vs_step_v1281.v1"
VERDICTS = (
    "relative_step_sets_the_clock",
    "small_norm_speeds_grokking_beyond_lr",
    "large_norm_speeds_grokking_beyond_lr",
    "review",
)


@dataclass(frozen=True)
class StepClockConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    width: int = 128
    max_steps: int = 60000
    base_lr: float = 1e-3
    # verdict arm: alpha=1 at the relative steps v1280's rescued cells took
    verdict_lrs: tuple[float, ...] = (4e-3, 8e-3)
    # pair map: verdict lr -> the v1280 reference (alpha=0.5) lr at the same r
    pair_ref_lrs: tuple[float, ...] = (2e-3, 4e-3)
    verdict_seeds: tuple[int, ...] = (1337, 1338, 1339)
    dose_lr: float = 2e-3
    sym_alpha: float = 2.0
    sym_lr: float = 8e-3
    side_seeds: tuple[int, ...] = (1337, 1338)
    grok_bar: float = 0.90
    heldout_bar: float = 0.90
    mem_bar: float = 0.99
    tgen_bars: tuple[float, ...] = (0.85, 0.90, 0.95)
    parity_band: tuple[float, float] = (0.5, 2.0)
    # G0 anchors, re-derived from the committed caches at bar 0.90
    ref80_medians: tuple[float, ...] = (3900.0, 1800.0)
    ref79_baseline_median: float = 11400.0
    max_runs: int = 12

    def validate(self) -> None:
        if len(self.verdict_lrs) != len(self.pair_ref_lrs) or len(self.verdict_lrs) != 2:
            raise ValueError("exactly two matched pairs are preregistered")
        for lr, ref_lr in zip(self.verdict_lrs, self.pair_ref_lrs):
            if not math.isclose(lr, 2 * ref_lr):
                raise ValueError("pair must match relative step: lr = 2 * ref_lr")
        if not math.isclose(self.sym_lr / self.sym_alpha, self.verdict_lrs[0]):
            raise ValueError("symmetry arm must sit at the r=4x relative step")
        if self.grok_bar not in self.tgen_bars:
            raise ValueError("grok_bar must be on the robustness grid")
        if not 0 < self.parity_band[0] < 1 < self.parity_band[1]:
            raise ValueError("parity band must bracket 1")
        if self.planned_runs() > self.max_runs:
            raise ValueError("planned cells exceed the GPU budget")

    def planned_runs(self) -> int:
        return (len(self.verdict_lrs) * len(self.verdict_seeds)
                + 2 * len(self.side_seeds))


# ---------------------------------------------------------------- phase A ----
def run_phase_a(cfg: StepClockConfig, device, trainer=train_cell,
                preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["alpha"], c["lr"], c["seed"]): dict(c) for c in preloaded}

    def cell_for(alpha: float, lr: float, seed: int, arm: str) -> dict:
        base = done.get((alpha, lr, seed)) or trainer(cfg, alpha, lr, seed, device)
        return base | {"arm": arm}

    cells: list[dict] = []
    for lr in cfg.verdict_lrs:
        for seed in cfg.verdict_seeds:
            cells.append(cell_for(1.0, lr, seed, "verdict"))
    for seed in cfg.side_seeds:
        cells.append(cell_for(1.0, cfg.dose_lr, seed, "dose"))
    for seed in cfg.side_seeds:
        cells.append(cell_for(cfg.sym_alpha, cfg.sym_lr, seed, "symmetry"))
    return {"schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": asdict(cfg), "cells": cells}


# ----------------------------------------------------------------- decide ----
def _ref80_cells(ref80: dict, ref_lr: float) -> list[dict]:
    return [c for c in ref80["cells"] if c["alpha"] == 0.5 and c["lr"] == ref_lr]


def _ref79_baseline(ref79: dict, cfg: StepClockConfig) -> list[dict]:
    return [c for c in ref79["cells"]
            if c["arm"] == "grid" and c["width"] == cfg.width and c["alpha"] == 1.0]


def _g0_references(ref80: dict, ref79: dict, cfg: StepClockConfig) -> bool:
    for ref_lr, anchor in zip(cfg.pair_ref_lrs, cfg.ref80_medians):
        cells = _ref80_cells(ref80, ref_lr)
        if len(cells) != 2:
            return False
        if any(classify(c, cfg.grok_bar, cfg) != "grokked" for c in cells):
            return False
        if _median([cell_tgen(c, cfg.grok_bar) for c in cells]) != anchor:
            return False
    base = _ref79_baseline(ref79, cfg)
    if len(base) != 3 or any(classify(c, cfg.grok_bar, cfg) != "grokked"
                             for c in base):
        return False
    return _median([cell_tgen(c, cfg.grok_bar)
                    for c in base]) == cfg.ref79_baseline_median


def _g1_complete(cache: dict, cfg: StepClockConfig) -> bool:
    counts = {"verdict": len(cfg.verdict_lrs) * len(cfg.verdict_seeds),
              "dose": len(cfg.side_seeds), "symmetry": len(cfg.side_seeds)}
    for arm, expected in counts.items():
        if len([c for c in cache["cells"] if c["arm"] == arm]) != expected:
            return False
    return True


def _pair_state(cache: dict, ref80: dict, cfg: StepClockConfig, lr: float,
                ref_lr: float, bar: float) -> tuple[str, float]:
    """('broken'|'ok', rho) for one matched pair at one bar."""
    mine = [c for c in cache["cells"] if c["arm"] == "verdict" and c["lr"] == lr]
    if any(classify(c, bar, cfg) == "broken" for c in mine):
        return "broken", math.inf
    my_median = _median([cell_tgen(c, bar) for c in mine])
    ref_median = _median([cell_tgen(c, bar) for c in _ref80_cells(ref80, ref_lr)])
    return "ok", my_median / ref_median


def _verdict_at_bar(cache: dict, ref80: dict, cfg: StepClockConfig,
                    bar: float) -> str:
    lo, hi = cfg.parity_band
    rhos = []
    for lr, ref_lr in zip(cfg.verdict_lrs, cfg.pair_ref_lrs):
        state, rho = _pair_state(cache, ref80, cfg, lr, ref_lr, bar)
        if state == "broken":
            return "review"
        rhos.append(rho)
    if all(lo <= r <= hi for r in rhos):
        return "relative_step_sets_the_clock"
    if all(r > hi for r in rhos):
        return "small_norm_speeds_grokking_beyond_lr"
    if all(r < lo for r in rhos):
        return "large_norm_speeds_grokking_beyond_lr"
    return "review"


def decide(cache: dict, ref80: dict, ref79: dict,
           cfg: StepClockConfig | None = None) -> dict:
    cfg = cfg or StepClockConfig()
    cfg.validate()
    info: dict = {"g0_references": _g0_references(ref80, ref79, cfg),
                  "g1_complete": _g1_complete(cache, cfg)}
    if not info["g0_references"]:
        return info | {"verdict": "review", "reason": "reference_cache_invalid",
                       "g2_bar_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_bar_stable": False}
    by_bar = {bar: _verdict_at_bar(cache, ref80, cfg, bar)
              for bar in cfg.tgen_bars}
    info["verdict_by_bar"] = by_bar
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    pairs = {}
    for lr, ref_lr in zip(cfg.verdict_lrs, cfg.pair_ref_lrs):
        state, rho = _pair_state(cache, ref80, cfg, lr, ref_lr, cfg.grok_bar)
        pairs[str(lr)] = {"state": state,
                          "rho": None if math.isinf(rho) else round(rho, 4)}
    info["pairs"] = pairs
    if info["g2_bar_stable"]:
        verdict = by_bar[cfg.grok_bar]
        reason = "broken_cells" if (verdict == "review"
                                    and any(p["state"] == "broken"
                                            for p in pairs.values())) else \
            ("mixed_pairs" if verdict == "review" else "")
        info |= {"verdict": verdict, "reason": reason}
    else:
        info |= {"verdict": "review", "reason": "bar_instability"}
    return info


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, ref80: dict, ref79: dict, info: dict,
                 cfg: StepClockConfig | None = None) -> dict:
    cfg = cfg or StepClockConfig()
    rows = []
    for c in cache["cells"]:
        t = cell_tgen(c, cfg.grok_bar)
        rows.append({"arm": c["arm"], "alpha": c["alpha"], "lr": c["lr"],
                     "seed": c["seed"], "class": classify(c, cfg.grok_bar, cfg),
                     "t_gen": None if math.isinf(t) else int(t),
                     "t_mem": c["t_mem"], "heldout_acc": c["heldout_acc"]})
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_frozen_recipe_60k_budget",
        "g0_references": info["g0_references"], "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "pairs": info.get("pairs", {}),
        "parity_band": list(cfg.parity_band),
        "ref80_medians": list(cfg.ref80_medians),
        "ref79_baseline_median": cfg.ref79_baseline_median,
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_references']} g1={s['g1_complete']}"
             f" g2={s['g2_bar_stable']} parity_band={s['parity_band']}"]
    for lr, pair in s["pairs"].items():
        lines.append(f"pair lr={lr}: state={pair['state']} rho={pair['rho']}")
    for row in report["cells"]:
        lines.append(f"{row['arm']} a={row['alpha']} lr={row['lr']}"
                     f" seed={row['seed']}: {row['class']} t_gen={row['t_gen']}"
                     f" t_mem={row['t_mem']} heldout={row['heldout_acc']}")
    return lines


def plot_result(cache: dict, ref80: dict, ref79: dict, info: dict, path) -> None:
    """One figure: matched pairs at r=4x/8x (left); alpha=1 lr dose (right)."""
    plt = agg_pyplot()

    cfg = StepClockConfig()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))

    def scatter(ax, x, cell, color, marker="o", size=45):
        t = cell_tgen(cell, cfg.grok_bar)
        y = cfg.max_steps * 1.15 if math.isinf(t) else t
        ax.scatter(x, y, color=color, marker=marker, s=size, zorder=3)

    labels = []
    for i, (lr, ref_lr) in enumerate(zip(cfg.verdict_lrs, cfg.pair_ref_lrs)):
        for c in _ref80_cells(ref80, ref_lr):
            scatter(ax1, 3 * i, c, "tab:orange")
        for c in (x for x in cache["cells"]
                  if x["arm"] == "verdict" and x["lr"] == lr):
            scatter(ax1, 3 * i + 1, c, "tab:blue")
        labels += [f"a=0.5\nlr={ref_lr}", f"a=1\nlr={lr}"]
    for c in (x for x in cache["cells"] if x["arm"] == "symmetry"):
        scatter(ax1, 2, c, "tab:purple", marker="s")
    labels.insert(2, f"a=2\nlr={cfg.sym_lr}")
    ax1.axhline(cfg.ref79_baseline_median, color="gray", linestyle="--",
                label="a=1 lr=1e-3 baseline (11,400)")
    ax1.axhline(cfg.max_steps, color="gray", linestyle=":",
                label="60k budget (censored above)")
    ax1.set_xticks([0, 1, 2, 3, 4], labels)
    ax1.set(yscale="log", ylabel="t_gen (steps, log)",
            title="matched relative step: r=4x (left 3), r=8x (right 2)")
    ax1.legend(fontsize=7)

    dose_pts = [(cfg.base_lr, c) for c in _ref79_baseline(ref79, cfg)]
    dose_pts += [(c["lr"], c) for c in cache["cells"]
                 if c["arm"] in ("verdict", "dose")]
    for lr, c in dose_pts:
        color = "gray" if lr == cfg.base_lr else "tab:blue"
        scatter(ax2, lr, c, color)
    ax2.axhline(cfg.max_steps, color="gray", linestyle=":")
    ax2.set(xscale="log", yscale="log", xlabel="lr (log)",
            ylabel="t_gen (steps, log)",
            title="alpha=1 lr dose (gray = v1279 baseline)")
    fig.suptitle(f"v1281 norm vs step: {info['verdict']}", fontsize=11)

    fig.tight_layout()
    save_figure(fig, path)
