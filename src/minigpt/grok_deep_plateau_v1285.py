"""v1285: the deep plateau -- does canonical grokking sculpt, or wait?

v1284 showed both dynamical phases build the Fourier circuit on one relative
schedule (F ~ 0.25) at boundary widths, where plateaus are short and leaky.
This version runs the identical measurement on the classic deep plateau --
d=128 at the canonical recipe (t_mem=100, t_gen 10,500-12,700) -- reusing
v1284's snapshot machinery unchanged, with t_pre bars raised to {0.25, 0.30,
0.35} because the canonical plateau rests at val ~0.11-0.21, not chance
(P1-disclosed adaptation).

Preregistered before any GPU run (see docs/v1285-deep-plateau-brief.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from minigpt.grok_arc_common import agg_pyplot, median as _median, save_figure
from minigpt.grok_circuit_timing_v1284 import (
    run_cell,
    structure_fraction,
    train_snapshot,
)
from minigpt.grok_delay_gate_v1283 import classify_phase

SCHEMA = "grok_deep_plateau_v1285.v1"
VERDICTS = (
    "deep_plateau_sculpts",
    "construction_is_late_everywhere",
    "partial_early_construction",
    "review",
)


@dataclass(frozen=True)
class DeepPlateauConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    lr: float = 1e-3
    width: int = 128
    max_steps: int = 60000
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    ladder: tuple[int, ...] = (100, 200, 400, 700, 1000, 1400, 1900, 2600,
                               3400, 4400, 5600, 7000, 8600, 10400, 12400)
    top_k: int = 5
    heldout_bar: float = 0.90
    phase_pair: tuple[float, float] = (0.5, 0.7)
    f_low: float = 0.2
    f_high: float = 0.5
    pre_bar: float = 0.30
    pre_bars: tuple[float, ...] = (0.25, 0.30, 0.35)
    heldout_tol: float = 1e-6
    max_runs: int = 50
    max_total_steps: int = 240000

    def validate(self) -> None:
        if self.width % self.n_head:
            raise ValueError("width must be divisible by n_head")
        if list(self.ladder) != sorted(self.ladder) or any(
                k % 100 for k in self.ladder):
            raise ValueError("ladder must be ascending multiples of eval_every")
        if not 0 < self.f_low < self.f_high <= 1:
            raise ValueError("need 0 < f_low < f_high <= 1")
        if self.pre_bar not in self.pre_bars:
            raise ValueError("pre_bar must be on the robustness grid")
        if len(self.seeds) != 3:
            raise ValueError("exactly three seeds are preregistered")
        if len(self.seeds) * (1 + len(self.ladder)) > self.max_runs:
            raise ValueError("worst-case run count exceeds the budget")


# ---------------------------------------------------------------- phase A ----
def run_phase_a(cfg: DeepPlateauConfig, device, snapshot_fn=train_snapshot,
                preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["width"], c["seed"]): dict(c) for c in preloaded}
    cells, runs, steps = [], 0, 0
    for seed in cfg.seeds:
        cell = done.get((cfg.width, seed)) or \
            run_cell(cfg, cfg.width, seed, "delayed", device, snapshot_fn)
        runs += 1 + len(cell["snapshots"])
        steps += cell["steps_run"] + sum(s["k"] for s in cell["snapshots"])
        if runs > cfg.max_runs or steps > cfg.max_total_steps:
            raise RuntimeError("trajectory budget exceeded")
        cells.append(cell)
    return {"schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": asdict(cfg), "cells": cells,
            "runs": runs, "total_steps": steps}


# ----------------------------------------------------------------- decide ----
def _reference_cells(reference: dict, cfg: DeepPlateauConfig) -> dict:
    return {c["seed"]: c for c in reference["cells"]
            if c["arm"] == "grid" and c["width"] == cfg.width
            and c["alpha"] == 1.0}


def _g0(cache: dict, reference: dict, cfg: DeepPlateauConfig) -> str:
    refs = _reference_cells(reference, cfg)
    for cell in cache["cells"]:
        ref = refs.get(cell["seed"])
        if not cell["prefix_ok"]:
            return "prefix_nondeterministic"
        if ref is None or cell["t_mem"] != ref["t_mem"] \
                or cell["t_gen"] != ref["t_gen"] \
                or abs(cell["heldout_acc"] - ref["heldout_acc"]) > cfg.heldout_tol:
            return "reference_mismatch"
        if cell["heldout_acc"] < cfg.heldout_bar:
            return "substrate_unsound"
        if classify_phase(cell, cfg.phase_pair, cfg) != "delayed":
            return "phase_mismatch"
    return ""


def _g1(cache: dict, cfg: DeepPlateauConfig) -> bool:
    if len(cache["cells"]) != len(cfg.seeds):
        return False
    for cell in cache["cells"]:
        expected = [k for k in cfg.ladder if k < cell["steps_run"]]
        if [s["k"] for s in cell["snapshots"]] != expected:
            return False
    return True


def _verdict_at_bar(fractions: list[float], cfg: DeepPlateauConfig) -> str:
    if min(fractions) <= cfg.f_low and max(fractions) >= cfg.f_high:
        return "review"  # mixed_seeds dispersion guard
    med = _median(fractions)
    if med >= cfg.f_high:
        return "deep_plateau_sculpts"
    if med <= cfg.f_low:
        return "construction_is_late_everywhere"
    return "partial_early_construction"


def decide(cache: dict, reference: dict,
           cfg: DeepPlateauConfig | None = None) -> dict:
    cfg = cfg or DeepPlateauConfig()
    cfg.validate()
    g0_reason = _g0(cache, reference, cfg)
    info: dict = {"g0_ok": g0_reason == "", "g1_complete": _g1(cache, cfg)}
    if g0_reason:
        return info | {"verdict": "review", "reason": g0_reason,
                       "g2_bar_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_bar_stable": False}
    by_bar = {}
    for bar in cfg.pre_bars:
        fractions = [structure_fraction(c, bar) for c in cache["cells"]]
        by_bar[bar] = _verdict_at_bar(fractions, cfg)
    info["verdict_by_bar"] = {str(b): v for b, v in by_bar.items()}
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    primary = [structure_fraction(c, cfg.pre_bar) for c in cache["cells"]]
    info["fractions"] = {str(c["seed"]): round(f, 4)
                         for c, f in zip(cache["cells"], primary)}
    info["f_median"] = round(_median(primary), 4)
    if info["g2_bar_stable"]:
        verdict = by_bar[cfg.pre_bar]
        reason = "mixed_seeds" if verdict == "review" else ""
        info |= {"verdict": verdict, "reason": reason}
    else:
        info |= {"verdict": "review", "reason": "bar_instability"}
    return info


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, reference: dict, info: dict,
                 cfg: DeepPlateauConfig | None = None) -> dict:
    cfg = cfg or DeepPlateauConfig()
    rows = []
    for c in cache["cells"]:
        gen = c["t_gen"]
        by_step = {s["k"]: s["share"] for s in c["snapshots"]}

        def share_near(target):
            below = [k for k in by_step if k <= target]
            return by_step[max(below)] if below else None

        rows.append({"seed": c["seed"],
                     "fraction": round(structure_fraction(c, cfg.pre_bar), 4),
                     "c0_share": c["c0_share"], "final_share": c["final_share"],
                     "share_quarter": share_near(gen * 0.25),
                     "share_half": share_near(gen * 0.5),
                     "share_three_quarter": share_near(gen * 0.75),
                     "t_mem": c["t_mem"], "t_gen": gen,
                     "heldout_acc": c["heldout_acc"],
                     "snapshot_count": len(c["snapshots"])})
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_canonical_recipe_d128",
        "g0_ok": info["g0_ok"], "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "fractions": info.get("fractions", {}),
        "f_median": info.get("f_median"),
        "runs": cache.get("runs"), "total_steps": cache.get("total_steps"),
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_ok']} g1={s['g1_complete']} g2={s['g2_bar_stable']}"
             f" runs={s['runs']} total_steps={s['total_steps']}",
             f"f_median={s['f_median']} fractions={s['fractions']}"]
    for row in report["cells"]:
        lines.append(f"seed={row['seed']}: F={row['fraction']}"
                     f" c0={row['c0_share']} final={row['final_share']}"
                     f" C@25/50/75%t_gen={row['share_quarter']}/"
                     f"{row['share_half']}/{row['share_three_quarter']}"
                     f" t_mem={row['t_mem']} t_gen={row['t_gen']}"
                     f" heldout={row['heldout_acc']}")
    return lines


def plot_result(cache: dict, info: dict, path) -> None:
    """One figure: the three deep-plateau C(t) trajectories, val faint,
    t_mem/t_gen marked."""
    plt = agg_pyplot()

    fig, ax = plt.subplots(figsize=(8.5, 5))
    colors = ("tab:blue", "tab:orange", "tab:purple")
    for c, color in zip(cache["cells"], colors):
        xs = [s["k"] for s in c["snapshots"]] + [c["steps_run"]]
        ys = [s["share"] for s in c["snapshots"]] + [c["final_share"]]
        ax.plot(xs, ys, color=color, linewidth=1.6, marker="o", markersize=3,
                label=f"seed {c['seed']} (t_gen {c['t_gen']})")
        ax.plot([r[0] for r in c["curve"]], [r[2] for r in c["curve"]],
                color=color, alpha=0.18, linewidth=0.8)
        ax.axvline(c["t_gen"], color=color, alpha=0.35, linestyle=":")
    ax.axvline(cache["cells"][0]["t_mem"], color="gray", alpha=0.6,
               linestyle="--", label=f"t_mem ({cache['cells'][0]['t_mem']})")
    ax.set(xscale="log", xlabel="training step (log)",
           ylabel="final-circuit power share C(t)  /  val acc (faint)",
           ylim=(0, 1.02),
           title=f"v1285 deep plateau: {info['verdict']}")
    ax.legend(fontsize=7)
    fig.tight_layout()
    save_figure(fig, path)
