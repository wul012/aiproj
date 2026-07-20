"""v1283: the delayed phase is width-gated -- where does grokking switch on?

P1 forensics over the v1279-v1282 caches established that the grokking phase
structure (a memorized-not-generalizing plateau) survives every stable lr at
d=128 (the delay compresses ~11,100 -> ~700 steps but never vanishes), while
w=16 is coupled -- train and val rise together -- at BOTH lr=1e-3 and 4e-3.
The gate is width, not lr. This version maps it: widths {20, 24, 28} at the
canonical recipe, with re-run w=16/32 anchors carrying full train curves.

Preregistered before any GPU run (see docs/v1283-delay-gate-brief.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone

from minigpt.grok_arc_common import agg_pyplot, save_figure
from minigpt.grok_init_rescue_v1280 import train_cell

SCHEMA = "grok_delay_gate_v1283.v1"
VERDICTS = (
    "delayed_phase_onset_is_sharp",
    "delayed_phase_onset_is_graded",
    "review",
)
PHASES = ("coupled", "intermediate", "delayed", "failed")


@dataclass(frozen=True)
class DelayGateConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    width: int = 128          # placeholder; every cell overrides via replace
    max_steps: int = 60000
    lr: float = 1e-3          # the canonical recipe -- this version varies width
    boundary_widths: tuple[int, ...] = (20, 24, 28)
    anchor_widths: tuple[int, ...] = (16, 32)
    anchor_expected: tuple[str, ...] = ("coupled", "delayed")
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    anchor_seeds: tuple[int, ...] = (1337, 1338)
    heldout_bar: float = 0.90
    # threshold pairs (coupled_max, delayed_min), both inside the P1 bimodal
    # hole [0.41, 0.79]; first pair is primary, verdict must agree on all
    threshold_pairs: tuple[tuple[float, float], ...] = ((0.5, 0.7), (0.4, 0.8))
    max_failed_per_width: int = 1
    max_runs: int = 16

    def validate(self) -> None:
        for w in self.boundary_widths + self.anchor_widths:
            if w % self.n_head:
                raise ValueError("every width must be divisible by n_head")
        if sorted(self.boundary_widths) != list(self.boundary_widths):
            raise ValueError("boundary widths must be ascending")
        if len(self.anchor_widths) != 2 or len(self.anchor_expected) != 2:
            raise ValueError("exactly two anchors with expected classes")
        if not (self.anchor_widths[0] < self.boundary_widths[0]
                and self.boundary_widths[-1] < self.anchor_widths[1]):
            raise ValueError("anchors must bracket the boundary widths")
        for c, d in self.threshold_pairs:
            if not 0 < c < d < 1:
                raise ValueError("threshold pairs must satisfy 0 < c < d < 1")
        planned = (len(self.boundary_widths) * len(self.seeds)
                   + len(self.anchor_widths) * len(self.anchor_seeds))
        if planned > self.max_runs:
            raise ValueError("planned cells exceed the GPU budget")


# ------------------------------------------------------------ phase classes ----
def max_train_val_gap(cell: dict) -> float:
    return max(float(r[1]) - float(r[2]) for r in cell["curve"])


def classify_phase(cell: dict, pair: tuple[float, float],
                   cfg: DelayGateConfig) -> str:
    if cell["heldout_acc"] < cfg.heldout_bar:
        return "failed"
    gap = max_train_val_gap(cell)
    coupled_max, delayed_min = pair
    if gap <= coupled_max:
        return "coupled"
    return "delayed" if gap >= delayed_min else "intermediate"


# ---------------------------------------------------------------- phase A ----
def run_phase_a(cfg: DelayGateConfig, device, trainer=train_cell,
                preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["width"], c["seed"]): dict(c) for c in preloaded}

    def cell_for(width: int, seed: int, arm: str) -> dict:
        base = done.get((width, seed)) or \
            trainer(replace(cfg, width=width), 1.0, cfg.lr, seed, device)
        return base | {"arm": arm, "width": width}

    cells: list[dict] = []
    for width in cfg.boundary_widths:
        for seed in cfg.seeds:
            cells.append(cell_for(width, seed, "boundary"))
    for width in cfg.anchor_widths:
        for seed in cfg.anchor_seeds:
            cells.append(cell_for(width, seed, "anchor"))
    return {"schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": asdict(cfg), "cells": cells}


# ----------------------------------------------------------------- decide ----
def _width_cells(cache: dict, arm: str, width: int) -> list[dict]:
    return [c for c in cache["cells"] if c["arm"] == arm and c["width"] == width]


def _g0_anchors(cache: dict, cfg: DelayGateConfig,
                pair: tuple[float, float]) -> bool:
    for width, expected in zip(cfg.anchor_widths, cfg.anchor_expected):
        cells = _width_cells(cache, "anchor", width)
        if len(cells) != len(cfg.anchor_seeds):
            return False
        if any(classify_phase(c, pair, cfg) != expected for c in cells):
            return False
    return True


def _g1_complete(cache: dict, cfg: DelayGateConfig) -> bool:
    for width in cfg.boundary_widths:
        if len(_width_cells(cache, "boundary", width)) != len(cfg.seeds):
            return False
    total = (len(cfg.boundary_widths) * len(cfg.seeds)
             + len(cfg.anchor_widths) * len(cfg.anchor_seeds))
    return len(cache["cells"]) == total


def _width_class(cells: list[dict], pair: tuple[float, float],
                 cfg: DelayGateConfig) -> str:
    classes = [classify_phase(c, pair, cfg) for c in cells]
    if classes.count("failed") > cfg.max_failed_per_width:
        return "failed"
    live = [k for k in classes if k != "failed"]
    if live and all(k == live[0] for k in live):
        return live[0]
    return "mixed"


def _verdict_at_pair(cache: dict, cfg: DelayGateConfig,
                     pair: tuple[float, float]) -> tuple[str, str]:
    classes = [_width_class(_width_cells(cache, "boundary", w), pair, cfg)
               for w in cfg.boundary_widths]
    if any(k == "failed" for k in classes):
        return "review", "substrate_unsound"
    if any(k == "mixed" for k in classes):
        return "review", "mixed_widths"
    order = {"coupled": 0, "intermediate": 1, "delayed": 2}
    ranks = [order[k] for k in classes]
    if ranks != sorted(ranks):
        return "review", "mixed_widths"
    if "intermediate" in classes:
        return "delayed_phase_onset_is_graded", ""
    return "delayed_phase_onset_is_sharp", ""


def decide(cache: dict, cfg: DelayGateConfig | None = None) -> dict:
    cfg = cfg or DelayGateConfig()
    cfg.validate()
    primary = cfg.threshold_pairs[0]
    info: dict = {"g0_anchors": _g0_anchors(cache, cfg, primary),
                  "g1_complete": _g1_complete(cache, cfg)}
    if not info["g0_anchors"]:
        return info | {"verdict": "review", "reason": "anchor_mismatch",
                       "g2_threshold_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_threshold_stable": False}
    by_pair = {str(pair): _verdict_at_pair(cache, cfg, pair)
               for pair in cfg.threshold_pairs}
    info["verdict_by_pair"] = {k: v[0] for k, v in by_pair.items()}
    info["g2_threshold_stable"] = len({v[0] for v in by_pair.values()}) == 1
    info["width_classes"] = {
        str(w): _width_class(_width_cells(cache, "boundary", w), primary, cfg)
        for w in cfg.boundary_widths}
    info["max_gap_by_cell"] = {
        f"{c['width']}/{c['seed']}": round(max_train_val_gap(c), 4)
        for c in cache["cells"]}
    if info["g2_threshold_stable"]:
        verdict, reason = by_pair[str(primary)]
        info |= {"verdict": verdict, "reason": reason}
    else:
        info |= {"verdict": "review", "reason": "threshold_instability"}
    return info


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, info: dict,
                 cfg: DelayGateConfig | None = None) -> dict:
    cfg = cfg or DelayGateConfig()
    primary = cfg.threshold_pairs[0]
    rows = []
    for c in cache["cells"]:
        t_gen = c["t_gen"]
        rows.append({"arm": c["arm"], "width": c["width"], "seed": c["seed"],
                     "phase": classify_phase(c, primary, cfg),
                     "max_gap": round(max_train_val_gap(c), 4),
                     "t_mem": c["t_mem"], "t_gen": t_gen,
                     "delay": (t_gen - c["t_mem"])
                     if (t_gen is not None and c["t_mem"] is not None) else None,
                     "heldout_acc": c["heldout_acc"]})
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_canonical_recipe_60k_budget",
        "g0_anchors": info["g0_anchors"], "g1_complete": info["g1_complete"],
        "g2_threshold_stable": info["g2_threshold_stable"],
        "width_classes": info.get("width_classes", {}),
        "threshold_pairs": [list(p) for p in cfg.threshold_pairs],
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_anchors']} g1={s['g1_complete']}"
             f" g2={s['g2_threshold_stable']}"
             f" thresholds={s['threshold_pairs']}"]
    for w, k in s["width_classes"].items():
        lines.append(f"width={w}: {k}")
    for row in report["cells"]:
        lines.append(f"{row['arm']} w={row['width']} seed={row['seed']}:"
                     f" {row['phase']} max_gap={row['max_gap']}"
                     f" t_mem={row['t_mem']} t_gen={row['t_gen']}"
                     f" delay={row['delay']} heldout={row['heldout_acc']}")
    return lines


def plot_result(cache: dict, info: dict, path) -> None:
    """One figure: max train-val gap vs width, threshold band, classes."""
    plt = agg_pyplot()

    cfg = DelayGateConfig()
    coupled_max, delayed_min = cfg.threshold_pairs[0]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    colors = {"coupled": "tab:green", "intermediate": "tab:orange",
              "delayed": "tab:blue", "failed": "black"}
    for c in cache["cells"]:
        phase = classify_phase(c, cfg.threshold_pairs[0], cfg)
        filled = c["arm"] == "boundary"
        kw = ({"facecolors": colors[phase], "edgecolors": colors[phase]}
              if filled else
              {"facecolors": "none", "edgecolors": colors[phase]})
        ax.scatter(c["width"], max_train_val_gap(c), s=55, zorder=3, **kw)
    ax.axhspan(coupled_max, delayed_min, color="gray", alpha=0.15,
               label=f"threshold band ({coupled_max}-{delayed_min}), "
                     "empty in P1 data")
    ax.set(xlabel="n_embd (width)", ylabel="max(train_acc - val_acc)",
           ylim=(0, 1.05),
           title=f"v1283 delay gate: {info['verdict']}")
    ax.set_xticks([16, 20, 24, 28, 32])
    handles = [plt.Line2D([], [], marker="o", color=col, linestyle="",
                          label=lab) for lab, col in colors.items()]
    handles.append(plt.Line2D([], [], marker="o", color="gray", linestyle="",
                              markerfacecolor="none",
                              label="anchors (w=16/32, hollow)"))
    ax.legend(handles=handles, fontsize=7, loc="center right")
    fig.tight_layout()
    save_figure(fig, path)
