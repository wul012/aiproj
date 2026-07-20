"""v1282: does the width clock collapse to lr?

v1277/v1279 found narrow models grok ~5x faster and d=64 is a catastrophic slow
zone -- both at the canonical lr=1e-3. v1281 showed that baseline is lr-starved
(d=128 collapses 11,400 -> ~1,400 at lr=4e-3). This version trains widths
{16, 32, 64} at lr=4e-3 against the v1281 d=128 reference: if all converge to
the same floor, the width effects were lr-regime artifacts and the v1277
question closes; a surviving narrow speedup or a surviving d=64 hole would be
genuinely width-specific.

Preregistered before any GPU run (see docs/v1282-width-lr-brief.md).
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone

from minigpt.grok_arc_common import agg_pyplot, median as _median, save_figure
from minigpt.grok_init_rescue_v1280 import cell_tgen, classify, train_cell

SCHEMA = "grok_width_lr_v1282.v1"
VERDICTS = (
    "width_clock_collapses_to_lr",
    "narrow_speedup_survives_lr",
    "mid_width_hole_survives_lr",
    "review",
)


@dataclass(frozen=True)
class WidthLrConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    width: int = 128          # reference width; verdict widths override via replace
    max_steps: int = 60000
    lr: float = 4e-3
    hole_lr: float = 8e-3
    verdict_widths: tuple[int, ...] = (16, 32, 64)
    hole_width: int = 64
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    hole_seeds: tuple[int, ...] = (1337, 1338)
    grok_bar: float = 0.90
    heldout_bar: float = 0.90
    mem_bar: float = 0.99
    tgen_bars: tuple[float, ...] = (0.85, 0.90, 0.95)
    parity_band: tuple[float, float] = (0.5, 2.0)
    # G0 anchors re-derived from the committed caches at bar 0.90
    ref81_median: float = 1400.0
    ref79_medians: tuple[tuple[int, float], ...] = ((16, 2800.0), (32, 2700.0),
                                                    (128, 11400.0))
    ref79_hole_min_censored: int = 2
    max_runs: int = 12

    def validate(self) -> None:
        if any(w % self.n_head for w in self.verdict_widths):
            raise ValueError("every verdict width must be divisible by n_head")
        if self.hole_width not in self.verdict_widths:
            raise ValueError("the hole probe must target a verdict width")
        if self.hole_lr <= self.lr:
            raise ValueError("the hole probe must raise the lr dose")
        if self.grok_bar not in self.tgen_bars:
            raise ValueError("grok_bar must be on the robustness grid")
        if not 0 < self.parity_band[0] < 1 < self.parity_band[1]:
            raise ValueError("parity band must bracket 1")
        planned = len(self.verdict_widths) * len(self.seeds) + len(self.hole_seeds)
        if planned > self.max_runs:
            raise ValueError("planned cells exceed the GPU budget")


# ---------------------------------------------------------------- phase A ----
def _hole_rule_fires(cells: list[dict], cfg: WidthLrConfig) -> bool:
    """Deterministic: >=2 of the d=64 verdict cells fail to grok."""
    hole = [c for c in cells
            if c["arm"] == "width" and c["width"] == cfg.hole_width]
    failed = sum(classify(c, cfg.grok_bar, cfg) != "grokked" for c in hole)
    return failed >= cfg.ref79_hole_min_censored


def run_phase_a(cfg: WidthLrConfig, device, trainer=train_cell,
                preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["width"], c["lr"], c["seed"]): dict(c) for c in preloaded}

    def cell_for(width: int, lr: float, seed: int, arm: str) -> dict:
        base = done.get((width, lr, seed)) or \
            trainer(replace(cfg, width=width), 1.0, lr, seed, device)
        return base | {"arm": arm, "width": width}

    cells: list[dict] = []
    for width in cfg.verdict_widths:
        for seed in cfg.seeds:
            cells.append(cell_for(width, cfg.lr, seed, "width"))
    if _hole_rule_fires(cells, cfg):
        for seed in cfg.hole_seeds:
            cells.append(cell_for(cfg.hole_width, cfg.hole_lr, seed, "hole_probe"))
    return {"schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": asdict(cfg), "cells": cells}


# ----------------------------------------------------------------- decide ----
def _ref81_cells(ref81: dict) -> list[dict]:
    return [c for c in ref81["cells"] if c["arm"] == "verdict" and c["lr"] == 4e-3]


def _g0_references(ref81: dict, ref79: dict, cfg: WidthLrConfig) -> bool:
    anchor = _ref81_cells(ref81)
    if len(anchor) != 3 or any(classify(c, cfg.grok_bar, cfg) != "grokked"
                               for c in anchor):
        return False
    if _median([cell_tgen(c, cfg.grok_bar) for c in anchor]) != cfg.ref81_median:
        return False
    for width, median in cfg.ref79_medians:
        cells = [c for c in ref79["cells"]
                 if c["arm"] == "grid" and c["width"] == width]
        finite = [cell_tgen(c, cfg.grok_bar) for c in cells
                  if math.isfinite(cell_tgen(c, cfg.grok_bar))]
        if len(cells) != 3 or not finite or _median(finite) != median:
            return False
    hole = [c for c in ref79["cells"]
            if c["arm"] == "grid" and c["width"] == cfg.hole_width]
    censored = sum(math.isinf(cell_tgen(c, cfg.grok_bar)) for c in hole)
    return len(hole) == 3 and censored >= cfg.ref79_hole_min_censored


def _g1_complete(cache: dict, cfg: WidthLrConfig) -> bool:
    width_cells = [c for c in cache["cells"] if c["arm"] == "width"]
    if len(width_cells) != len(cfg.verdict_widths) * len(cfg.seeds):
        return False
    probes = [c for c in cache["cells"] if c["arm"] == "hole_probe"]
    expected = len(cfg.hole_seeds) if _hole_rule_fires(width_cells, cfg) else 0
    return len(probes) == expected


def _width_state(cache: dict, ref81: dict, cfg: WidthLrConfig, width: int,
                 bar: float) -> str:
    cells = [c for c in cache["cells"]
             if c["arm"] == "width" and c["width"] == width]
    if any(classify(c, bar, cfg) == "broken" for c in cells):
        return "broken"
    ref_median = _median([cell_tgen(c, bar) for c in _ref81_cells(ref81)])
    rho = _median([cell_tgen(c, bar) for c in cells]) / ref_median
    lo, hi = cfg.parity_band
    if rho < lo:
        return "still_faster"
    return "converged" if rho <= hi else "still_slower"


def _verdict_at_bar(cache: dict, ref81: dict, cfg: WidthLrConfig,
                    bar: float) -> str:
    states = {w: _width_state(cache, ref81, cfg, w, bar)
              for w in cfg.verdict_widths}
    if any(s == "broken" for s in states.values()):
        return "review"
    narrow = [states[w] for w in cfg.verdict_widths if w != cfg.hole_width]
    hole = states[cfg.hole_width]
    if all(s == "converged" for s in states.values()):
        return "width_clock_collapses_to_lr"
    if any(s == "still_faster" for s in narrow) and hole != "still_slower":
        return "narrow_speedup_survives_lr"
    if hole == "still_slower" and all(s == "converged" for s in narrow):
        return "mid_width_hole_survives_lr"
    return "review"


def decide(cache: dict, ref81: dict, ref79: dict,
           cfg: WidthLrConfig | None = None) -> dict:
    cfg = cfg or WidthLrConfig()
    cfg.validate()
    info: dict = {"g0_references": _g0_references(ref81, ref79, cfg),
                  "g1_complete": _g1_complete(cache, cfg)}
    if not info["g0_references"]:
        return info | {"verdict": "review", "reason": "reference_cache_invalid",
                       "g2_bar_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_bar_stable": False}
    by_bar = {bar: _verdict_at_bar(cache, ref81, cfg, bar)
              for bar in cfg.tgen_bars}
    info["verdict_by_bar"] = by_bar
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    states = {str(w): _width_state(cache, ref81, cfg, w, cfg.grok_bar)
              for w in cfg.verdict_widths}
    info["width_states"] = states
    ref_median = _median([cell_tgen(c, cfg.grok_bar) for c in _ref81_cells(ref81)])
    rhos = {}
    for w in cfg.verdict_widths:
        cells = [c for c in cache["cells"]
                 if c["arm"] == "width" and c["width"] == w]
        rho = _median([cell_tgen(c, cfg.grok_bar) for c in cells]) / ref_median
        rhos[str(w)] = None if math.isinf(rho) else round(rho, 4)
    info["rho_by_width"] = rhos
    info["hole_rule_fired"] = _hole_rule_fires(
        [c for c in cache["cells"] if c["arm"] == "width"], cfg)
    if info["g2_bar_stable"]:
        verdict = by_bar[cfg.grok_bar]
        reason = ""
        if verdict == "review":
            reason = "broken_cells" if any(s == "broken"
                                           for s in states.values()) \
                else "mixed_widths"
        info |= {"verdict": verdict, "reason": reason}
    else:
        info |= {"verdict": "review", "reason": "bar_instability"}
    return info


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, ref81: dict, ref79: dict, info: dict,
                 cfg: WidthLrConfig | None = None) -> dict:
    cfg = cfg or WidthLrConfig()
    rows = []
    for c in cache["cells"]:
        t = cell_tgen(c, cfg.grok_bar)
        rows.append({"arm": c["arm"], "width": c["width"], "lr": c["lr"],
                     "seed": c["seed"], "class": classify(c, cfg.grok_bar, cfg),
                     "t_gen": None if math.isinf(t) else int(t),
                     "t_mem": c["t_mem"], "heldout_acc": c["heldout_acc"]})
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_frozen_recipe_60k_budget",
        "g0_references": info["g0_references"], "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "width_states": info.get("width_states", {}),
        "rho_by_width": info.get("rho_by_width", {}),
        "hole_rule_fired": info.get("hole_rule_fired", False),
        "parity_band": list(cfg.parity_band),
        "ref81_median": cfg.ref81_median,
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_references']} g1={s['g1_complete']}"
             f" g2={s['g2_bar_stable']} hole_rule_fired={s['hole_rule_fired']}"]
    for w, state in s["width_states"].items():
        lines.append(f"width={w}: {state} rho={s['rho_by_width'].get(w)}")
    for row in report["cells"]:
        lines.append(f"{row['arm']} w={row['width']} lr={row['lr']}"
                     f" seed={row['seed']}: {row['class']} t_gen={row['t_gen']}"
                     f" t_mem={row['t_mem']} heldout={row['heldout_acc']}")
    return lines


def plot_result(cache: dict, ref81: dict, ref79: dict, info: dict, path) -> None:
    """One figure: t_gen vs width -- lr=1e-3 (v1279, gray) vs lr=4e-3 (new)."""
    import matplotlib

    plt = agg_pyplot()

    cfg = WidthLrConfig()
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    seen: dict = {}

    def scatter(x, cell, color, marker="o", filled=True, label=None):
        t = cell_tgen(cell, cfg.grok_bar)
        if math.isinf(t):
            rank = seen.get((x, color), 0)
            seen[(x, color)] = rank + 1
            y = cfg.max_steps * (1.12 + 0.10 * rank)
        else:
            y = t
        kw = {"facecolors": color, "edgecolors": color} if filled else \
            {"facecolors": "none", "edgecolors": color}
        ax.scatter(x, y, marker=marker, s=45, zorder=3, label=label, **kw)

    for c in (x for x in ref79["cells"] if x["arm"] == "grid"):
        scatter(c["width"], c, "gray", filled=False)
    for c in (x for x in cache["cells"] if x["arm"] == "width"):
        scatter(c["width"], c, "tab:blue")
    for c in _ref81_cells(ref81):
        scatter(128, c, "tab:blue", filled=False)
    for c in (x for x in cache["cells"] if x["arm"] == "hole_probe"):
        scatter(c["width"] * 1.08, c, "tab:purple", marker="s")
    ax.axhline(cfg.max_steps, color="gray", linestyle=":",
               label="60k budget (censored above)")
    ax.set(xscale="log", yscale="log", xlabel="n_embd (width, log)",
           ylabel="t_gen (steps, log)",
           title=f"v1282 width x lr: {info['verdict']}")
    ax.set_xticks([16, 32, 64, 128], ["16", "32", "64", "128"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    handles = [plt.Line2D([], [], marker="o", color="gray", linestyle="",
                          markerfacecolor="none", label="lr=1e-3 (v1279)"),
               plt.Line2D([], [], marker="o", color="tab:blue", linestyle="",
                          label="lr=4e-3 (new; hollow = v1281 ref)")]
    if any(c["arm"] == "hole_probe" for c in cache["cells"]):
        handles.append(plt.Line2D([], [], marker="s", color="tab:purple",
                                  linestyle="",
                                  label="d=64 @ lr=8e-3 (conditional probe)"))
    ax.legend(handles=handles, fontsize=7)
    fig.tight_layout()
    save_figure(fig, path)
