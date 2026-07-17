"""v1286: lr compression -- is F invariant when the plateau shrinks 8x?

v1285 showed the canonical d=128 plateau sculpts (F ~ 0.6); v1281 showed the
same cells grok ~8x faster at higher lr. This version re-runs the eight v1281
alpha=1 cells (lr in {2e-3, 4e-3, 8e-3}) with snapshot ladders to test the
unified hypothesis: construction rate is set by the effective lr, and
generalization fires when construction completes -- in which case F is
preserved under compression. Machinery is v1284/v1285's unchanged; the t_pre
bars move to {0.10, 0.15, 0.20} because the compressed plateaus rest near zero
(P1-disclosed adaptation).

Preregistered before any GPU run (see docs/v1286-lr-compression-brief.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone

from minigpt.grok_circuit_timing_v1284 import (
    run_cell,
    structure_fraction,
    train_snapshot,
)
from minigpt.grok_delay_gate_v1283 import classify_phase

SCHEMA = "grok_lr_compression_v1286.v1"
VERDICTS = (
    "construction_completion_invariant",
    "compression_switches_to_late_construction",
    "partial_under_compression",
    "review",
)


@dataclass(frozen=True)
class LrCompressionConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    lr: float = 1e-3          # placeholder; every cell overrides via replace
    width: int = 128
    max_steps: int = 60000
    cells: tuple[tuple[float, tuple[int, ...]], ...] = (
        (2e-3, (1337, 1338)),
        (4e-3, (1337, 1338, 1339)),
        (8e-3, (1337, 1338, 1339)))
    ladder: tuple[int, ...] = (100, 200, 300, 400, 500, 600, 800, 1000,
                               1200, 1500, 1800, 2200, 2600)
    top_k: int = 5
    heldout_bar: float = 0.90
    phase_pair: tuple[float, float] = (0.5, 0.7)
    f_low: float = 0.2
    f_high: float = 0.5
    pre_bar: float = 0.15
    pre_bars: tuple[float, ...] = (0.10, 0.15, 0.20)
    heldout_tol: float = 1e-6
    max_runs: int = 112
    max_total_steps: int = 130000

    def validate(self) -> None:
        if self.width % self.n_head:
            raise ValueError("width must be divisible by n_head")
        if list(self.ladder) != sorted(self.ladder) or any(
                k % 100 for k in self.ladder):
            raise ValueError("ladder must be ascending multiples of eval_every")
        if len(self.cells) != 3 or any(not seeds for _lr, seeds in self.cells):
            raise ValueError("three lr groups, each with seeds, preregistered")
        if not 0 < self.f_low < self.f_high <= 1:
            raise ValueError("need 0 < f_low < f_high <= 1")
        if self.pre_bar not in self.pre_bars:
            raise ValueError("pre_bar must be on the robustness grid")
        worst = sum(len(seeds) for _lr, seeds in self.cells) \
            * (1 + len(self.ladder))
        if worst > self.max_runs:
            raise ValueError("worst-case run count exceeds the budget")


# ---------------------------------------------------------------- phase A ----
def run_phase_a(cfg: LrCompressionConfig, device, snapshot_fn=train_snapshot,
                preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["lr"], c["seed"]): dict(c) for c in preloaded}
    cells, runs, steps = [], 0, 0
    for lr, seeds in cfg.cells:
        for seed in seeds:
            cell = done.get((lr, seed))
            if cell is None:
                cell = run_cell(replace(cfg, lr=lr), cfg.width, seed,
                                "delayed", device, snapshot_fn)
                cell["lr"] = lr
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
def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def _reference_cells(reference: dict, cfg: LrCompressionConfig) -> dict:
    return {(c["lr"], c["seed"]): c for c in reference["cells"]
            if c.get("alpha") == 1.0}


def _g0(cache: dict, reference: dict, cfg: LrCompressionConfig) -> str:
    refs = _reference_cells(reference, cfg)
    for cell in cache["cells"]:
        ref = refs.get((cell["lr"], cell["seed"]))
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


def _g1(cache: dict, cfg: LrCompressionConfig) -> bool:
    expected_n = sum(len(seeds) for _lr, seeds in cfg.cells)
    if len(cache["cells"]) != expected_n:
        return False
    for cell in cache["cells"]:
        expected = [k for k in cfg.ladder if k < cell["steps_run"]]
        if [s["k"] for s in cell["snapshots"]] != expected:
            return False
    return True


def _bin_of(value: float, cfg: LrCompressionConfig) -> str:
    if value >= cfg.f_high:
        return "sculpt"
    return "late" if value <= cfg.f_low else "partial"


def _verdict_at_bar(cache: dict, cfg: LrCompressionConfig, bar: float) -> str:
    bins = []
    for lr, _seeds in cfg.cells:
        fractions = [structure_fraction(c, bar) for c in cache["cells"]
                     if c["lr"] == lr]
        if min(fractions) <= cfg.f_low and max(fractions) >= cfg.f_high:
            return "review"  # within-lr dispersion guard (mixed_seeds)
        bins.append(_bin_of(_median(fractions), cfg))
    if len(set(bins)) != 1:
        return "review"  # mixed_lrs
    return {"sculpt": "construction_completion_invariant",
            "late": "compression_switches_to_late_construction",
            "partial": "partial_under_compression"}[bins[0]]


def decide(cache: dict, reference: dict,
           cfg: LrCompressionConfig | None = None) -> dict:
    cfg = cfg or LrCompressionConfig()
    cfg.validate()
    g0_reason = _g0(cache, reference, cfg)
    info: dict = {"g0_ok": g0_reason == "", "g1_complete": _g1(cache, cfg)}
    if g0_reason:
        return info | {"verdict": "review", "reason": g0_reason,
                       "g2_bar_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_bar_stable": False}
    by_bar = {bar: _verdict_at_bar(cache, cfg, bar) for bar in cfg.pre_bars}
    info["verdict_by_bar"] = {str(b): v for b, v in by_bar.items()}
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    info["fractions"] = {f"{c['lr']}/{c['seed']}":
                         round(structure_fraction(c, cfg.pre_bar), 4)
                         for c in cache["cells"]}
    info["f_median_by_lr"] = {
        str(lr): round(_median([structure_fraction(c, cfg.pre_bar)
                                for c in cache["cells"] if c["lr"] == lr]), 4)
        for lr, _seeds in cfg.cells}
    if info["g2_bar_stable"]:
        verdict = by_bar[cfg.pre_bar]
        reason = ""
        if verdict == "review":
            groups = []
            for lr, _seeds in cfg.cells:
                fr = [structure_fraction(c, cfg.pre_bar)
                      for c in cache["cells"] if c["lr"] == lr]
                if min(fr) <= cfg.f_low and max(fr) >= cfg.f_high:
                    reason = "mixed_seeds"
                    break
                groups.append(_bin_of(_median(fr), cfg))
            reason = reason or "mixed_lrs"
        info |= {"verdict": verdict, "reason": reason}
    else:
        info |= {"verdict": "review", "reason": "bar_instability"}
    return info


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, reference: dict, info: dict,
                 cfg: LrCompressionConfig | None = None) -> dict:
    cfg = cfg or LrCompressionConfig()
    rows = []
    for c in cache["cells"]:
        rows.append({"lr": c["lr"], "seed": c["seed"],
                     "fraction": round(structure_fraction(c, cfg.pre_bar), 4),
                     "c0_share": c["c0_share"], "final_share": c["final_share"],
                     "t_mem": c["t_mem"], "t_gen": c["t_gen"],
                     "heldout_acc": c["heldout_acc"],
                     "snapshot_count": len(c["snapshots"])})
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_d128_compressed_lrs",
        "g0_ok": info["g0_ok"], "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "fractions": info.get("fractions", {}),
        "f_median_by_lr": info.get("f_median_by_lr", {}),
        "v1285_reference_medians": [0.720, 0.556, 0.600],
        "runs": cache.get("runs"), "total_steps": cache.get("total_steps"),
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_ok']} g1={s['g1_complete']} g2={s['g2_bar_stable']}"
             f" runs={s['runs']} total_steps={s['total_steps']}",
             f"f_median_by_lr={s['f_median_by_lr']}"
             f" (v1285 @1e-3: {s['v1285_reference_medians']})"]
    for key, frac in s["fractions"].items():
        lines.append(f"cell {key}: F={frac}")
    for row in report["cells"]:
        lines.append(f"lr={row['lr']} seed={row['seed']}: F={row['fraction']}"
                     f" c0={row['c0_share']} final={row['final_share']}"
                     f" t_mem={row['t_mem']} t_gen={row['t_gen']}"
                     f" heldout={row['heldout_acc']}")
    return lines


def plot_result(cache: dict, info: dict, path, v1285_cache: dict | None = None) -> None:
    """One figure: C versus relative time t/t_gen, colored by lr; v1285's
    1e-3 trajectories in gray for the compression-invariance comparison."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path as _Path

    fig, ax = plt.subplots(figsize=(8.5, 5))
    colors = {2e-3: "tab:green", 4e-3: "tab:blue", 8e-3: "tab:purple"}
    if v1285_cache:
        for c in v1285_cache["cells"]:
            xs = [s["k"] / c["t_gen"] for s in c["snapshots"]]
            ys = [s["share"] for s in c["snapshots"]]
            ax.plot(xs, ys, color="gray", alpha=0.5, linewidth=1.0,
                    label="lr=1e-3 (v1285)" if c is v1285_cache["cells"][0]
                    else None)
    for c in cache["cells"]:
        xs = [s["k"] / c["t_gen"] for s in c["snapshots"]]
        ys = [s["share"] for s in c["snapshots"]]
        ax.plot(xs, ys, color=colors[c["lr"]], linewidth=1.4, marker="o",
                markersize=3,
                label=f"lr={c['lr']}" if c["seed"] == 1337 else None)
    ax.axvline(1.0, color="gray", linestyle=":", alpha=0.7)
    ax.set(xlabel="relative time t / t_gen", xlim=(0, 1.6),
           ylabel="final-circuit power share C(t)",
           title=f"v1286 lr compression: {info['verdict']}")
    ax.legend(fontsize=7)
    fig.tight_layout()
    out = _Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)
