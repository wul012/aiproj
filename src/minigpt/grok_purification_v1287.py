"""v1287: post-grok purification -- does sculpting continue after grok?

v1286 inferred from endpoints that high-lr cells keep purifying after
generalization, but the P1 cache audit shows every cached run has near-zero
post-grok time (five cells early-stopped exactly at t_gen) -- all known purity
numbers are "purity at grok". This version extends the 11 v1285/v1286 cells to
a 3x t_gen horizon with early stop disabled (grok_stop_val above 1.0 -- a
config field, zero training-code modification) and watches the purity
trajectory directly. The fork: AdamW's stationarity condition is
lr-independent (universal equilibrium) vs a real lr-gated ceiling. Purity is
measured on each cell's COMMITTED cache top-5 set with the cached final_share
as the purity-at-grok anchor; the primary verdict is bar-free (climb +
convergence), the F_ext unification readout is secondary and cannot flip it.

Preregistered before any GPU run (see docs/v1287-purification-brief.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone

from minigpt.grok_checkpoint_v1185 import train_to_grok
from minigpt.grok_circuit_timing_v1284 import set_share
from minigpt.grok_delay_gate_v1283 import classify_phase
from minigpt.grok_interp_v1188 import embedding_spectrum, number_embedding
from minigpt.grok_predict_v1186 import evaluate_table
from minigpt.grok_speed_v1279 import scaled_init
from minigpt.grok_v1179 import GrokConfig

SCHEMA = "grok_purification_v1287.v1"
VERDICTS = ("purification_universal", "purification_lr_gated",
            "partial_purification", "review")
CANONICAL_LR = 1e-3


@dataclass(frozen=True)
class PurificationConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    width: int = 128
    lr: float = 1e-3          # placeholder; every cell overrides via replace
    cells: tuple[tuple[float, int, int], ...] = (
        (1e-3, 1337, 11400), (1e-3, 1338, 12700), (1e-3, 1339, 10500),
        (2e-3, 1337, 1900), (2e-3, 1338, 2800),
        (4e-3, 1337, 1400), (4e-3, 1338, 1800), (4e-3, 1339, 1000),
        (8e-3, 1337, 1000), (8e-3, 1338, 1400), (8e-3, 1339, 1500))
    multipliers: tuple[float, ...] = (1.4, 1.8, 2.4, 3.0)
    top_k: int = 5
    heldout_bar: float = 0.90
    phase_pair: tuple[float, float] = (0.5, 0.7)
    climb_bar: float = 0.10
    climb_bars: tuple[float, ...] = (0.05, 0.10, 0.15)
    conv_band: float = 0.15
    sat_tol: float = 0.02
    drop_guard: float = 0.05
    disp_guard: float = 0.30
    pre_bar_canonical: float = 0.30
    pre_bars_canonical: tuple[float, ...] = (0.25, 0.30, 0.35)
    pre_bar_compressed: float = 0.15
    pre_bars_compressed: tuple[float, ...] = (0.10, 0.15, 0.20)
    f_low: float = 0.2
    f_high: float = 0.5
    grok_stop_val: float = 2.0  # above 1.0 = early stop can never fire
    eval_every: int = 100
    max_runs: int = 48
    max_total_steps: int = 420000

    def validate(self) -> None:
        if self.width % self.n_head:
            raise ValueError("width must be divisible by n_head")
        if list(self.multipliers) != sorted(set(self.multipliers)) \
                or len(self.multipliers) < 2 or self.multipliers[0] <= 1.0:
            raise ValueError("multipliers must be ascending, distinct, > 1.0")
        if self.grok_stop_val <= 1.0:
            raise ValueError("grok_stop_val must exceed 1.0 (no early stop)")
        if not any(lr == CANONICAL_LR for lr, _s, _t in self.cells):
            raise ValueError("the canonical lr group must be present")
        if self.climb_bar not in self.climb_bars:
            raise ValueError("climb_bar must be on the robustness grid")
        if self.pre_bar_canonical not in self.pre_bars_canonical \
                or self.pre_bar_compressed not in self.pre_bars_compressed:
            raise ValueError("committed pre bars must be on their grids")
        if not 0 < self.f_low < self.f_high <= 1:
            raise ValueError("need 0 < f_low < f_high <= 1")
        total = 0
        for _lr, _seed, t_gen_ref in self.cells:
            if t_gen_ref <= 0 or t_gen_ref % self.eval_every:
                raise ValueError("t_gen_ref must be a positive eval multiple")
            ladder = [step_of(m, t_gen_ref) for m in self.multipliers]
            if ladder != sorted(set(ladder)):
                raise ValueError("derived ladder must be strictly ascending")
            total += sum(ladder)
        if len(self.cells) * len(self.multipliers) > self.max_runs:
            raise ValueError("run count exceeds the budget")
        if total > self.max_total_steps:
            raise ValueError("total step count exceeds the budget")


def step_of(multiplier: float, t_gen_ref: int) -> int:
    """Eval-grid-aligned absolute step for a relative multiplier."""
    return int((multiplier * t_gen_ref + 50) // 100) * 100


def group_lrs(cfg: PurificationConfig) -> tuple[float, ...]:
    seen: list[float] = []
    for lr, _seed, _t in cfg.cells:
        if lr not in seen:
            seen.append(lr)
    return tuple(seen)


# ------------------------------------------------------------- measurement ----
def _grok_cfg(cfg: PurificationConfig, seed: int, steps: int) -> GrokConfig:
    return GrokConfig(p=cfg.p, train_frac=cfg.train_frac, n_head=cfg.n_head,
                      n_embd=cfg.width, max_steps=steps, lr=cfg.lr,
                      grok_stop_val=cfg.grok_stop_val,
                      seeds=(seed,), wds=(cfg.weight_decay,))


def train_snapshot_ext(cfg: PurificationConfig, seed: int, steps: int,
                       horizon: int, device) -> dict:
    """One deterministic no-early-stop run; returns metrics + power spectrum."""
    init = scaled_init(cfg.width, seed, 1.0, cfg)
    model, meta, curve = train_to_grok(_grok_cfg(cfg, seed, steps), device,
                                       init_state=init)
    last = curve[-1]
    out = {"steps": int(last["step"]), "train_acc": float(last["train_acc"]),
           "val_acc": float(last["val_acc"]),
           "power": [float(x) for x in
                     embedding_spectrum(number_embedding(model, cfg.p))]}
    if steps >= horizon:  # the full run carries the endpoint extras
        out |= {"t_mem": meta.t_mem, "t_gen": meta.t_gen,
                "heldout_acc": float(evaluate_table(model, meta)["heldout_acc"]),
                "curve": [(int(r["step"]), float(r["train_acc"]),
                           float(r["val_acc"])) for r in curve]}
    return out


# ---------------------------------------------------------------- phase A ----
def run_cell(cfg: PurificationConfig, lr: float, seed: int, t_gen_ref: int,
             device, snapshot_fn=train_snapshot_ext) -> dict:
    cell_cfg = replace(cfg, lr=lr)
    ladder = [step_of(m, t_gen_ref) for m in cfg.multipliers]
    horizon = ladder[-1]
    full = snapshot_fn(cell_cfg, seed, horizon, horizon, device)
    curve_by_step = {row[0]: row for row in full["curve"]}
    snapshots, prefix_ok = [], True
    for k in ladder[:-1]:
        snap = snapshot_fn(cell_cfg, seed, k, horizon, device)
        row = curve_by_step.get(snap["steps"])
        ok = (row is not None
              and abs(row[1] - snap["train_acc"]) < 1e-9
              and abs(row[2] - snap["val_acc"]) < 1e-9)
        prefix_ok = prefix_ok and ok
        snapshots.append({"k": snap["steps"], "train_acc": snap["train_acc"],
                          "val_acc": snap["val_acc"], "power": snap["power"],
                          "prefix_ok": ok})
    return {"lr": lr, "seed": seed, "t_gen_ref": t_gen_ref, "ladder": ladder,
            "steps_run": full["steps"], "t_mem": full["t_mem"],
            "t_gen": full["t_gen"], "heldout_acc": full["heldout_acc"],
            "curve": full["curve"], "final_power": full["power"],
            "prefix_ok": prefix_ok, "snapshots": snapshots}


def run_phase_a(cfg: PurificationConfig, device,
                snapshot_fn=train_snapshot_ext, preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["lr"], c["seed"]): dict(c) for c in preloaded}
    cells, runs, steps = [], 0, 0
    for lr, seed, t_gen_ref in cfg.cells:
        cell = done.get((lr, seed)) or \
            run_cell(cfg, lr, seed, t_gen_ref, device, snapshot_fn)
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


def top_freqs(power: list[float], k: int) -> list[int]:
    return sorted(range(len(power)), key=lambda i: power[i], reverse=True)[:k]


def reference_map(ref_canonical: dict, ref_compressed: dict) -> dict:
    refs = {(CANONICAL_LR, c["seed"]): c for c in ref_canonical["cells"]}
    refs |= {(c["lr"], c["seed"]): c for c in ref_compressed["cells"]}
    return refs


def pre_bars_of(lr: float, cfg: PurificationConfig) -> tuple[float, ...]:
    return cfg.pre_bars_canonical if lr == CANONICAL_LR \
        else cfg.pre_bars_compressed


def pre_bar_of(lr: float, cfg: PurificationConfig) -> float:
    return cfg.pre_bar_canonical if lr == CANONICAL_LR \
        else cfg.pre_bar_compressed


def f_ext_of(ref: dict, c_final: float, bar: float) -> float:
    """v1284's structure fraction with the extended-horizon denominator; the
    pre-grok numerator is read from the committed cache's snapshots."""
    pre = [s for s in ref["snapshots"] if s["val_acc"] <= bar]
    denom = c_final - ref["c0_share"]
    if not pre or denom <= 0:
        return 0.0
    return min(1.0, max(0.0, (pre[-1]["share"] - ref["c0_share"]) / denom))


def cell_metrics(cell: dict, ref: dict, cfg: PurificationConfig) -> dict:
    top5_ref = ref["top5"]
    shares = [set_share(s["power"], top5_ref) for s in cell["snapshots"]]
    c_final = set_share(cell["final_power"], top5_ref)
    own5 = top_freqs(cell["final_power"], cfg.top_k)
    return {"anchor": ref["final_share"], "c0": ref["c0_share"],
            "shares": [round(v, 6) for v in shares],
            "c_final": round(c_final, 6),
            "own_final": round(set_share(cell["final_power"], own5), 6),
            "climb": round(c_final - ref["final_share"], 6),
            "set_match": sorted(own5) == sorted(top5_ref),
            "saturated": abs(c_final - shares[-1]) < cfg.sat_tol,
            "f_ext": {str(bar): round(f_ext_of(ref, c_final, bar), 4)
                      for bar in pre_bars_of(cell["lr"], cfg)}}


def _g0(cache: dict, refs: dict, cfg: PurificationConfig) -> str:
    for cell in cache["cells"]:
        ref = refs.get((cell["lr"], cell["seed"]))
        if ref is None:
            return "reference_mismatch"
        if not cell["prefix_ok"]:
            return "prefix_nondeterministic"
        if cell["steps_run"] != cell["ladder"][-1]:
            return "early_stop_fired"
        curve_by_step = {row[0]: row for row in cell["curve"]}
        prefix = all(
            (new := curve_by_step.get(int(step))) is not None
            and abs(new[1] - train) < 1e-9 and abs(new[2] - val) < 1e-9
            for step, train, val in ref["curve"])
        if cell["t_mem"] != ref["t_mem"] or cell["t_gen"] != ref["t_gen"] \
                or not prefix:
            return "reference_mismatch"
        if cell["heldout_acc"] < cfg.heldout_bar:
            return "substrate_unsound"
        if classify_phase(cell, cfg.phase_pair, cfg) != "delayed":
            return "phase_mismatch"
    return ""


def _g1(cache: dict, cfg: PurificationConfig) -> bool:
    if len(cache["cells"]) != len(cfg.cells):
        return False
    for cell, (lr, seed, t_gen_ref) in zip(cache["cells"], cfg.cells):
        ladder = [step_of(m, t_gen_ref) for m in cfg.multipliers]
        if (cell["lr"], cell["seed"]) != (lr, seed) \
                or cell["ladder"] != ladder \
                or [s["k"] for s in cell["snapshots"]] != ladder[:-1]:
            return False
    return True


def decide(cache: dict, ref_canonical: dict, ref_compressed: dict,
           cfg: PurificationConfig | None = None) -> dict:
    cfg = cfg or PurificationConfig()
    cfg.validate()
    refs = reference_map(ref_canonical, ref_compressed)
    g0_reason = _g0(cache, refs, cfg)
    info: dict = {"g0_ok": g0_reason == "", "g1_complete": _g1(cache, cfg)}
    if g0_reason:
        return info | {"verdict": "review", "reason": g0_reason,
                       "g2_bar_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_bar_stable": False}
    metrics = {(c["lr"], c["seed"]): cell_metrics(c, refs[(c["lr"], c["seed"])],
                                                  cfg)
               for c in cache["cells"]}
    groups = {lr: [metrics[(l, s)] for l, s, _t in cfg.cells if l == lr]
              for lr in group_lrs(cfg)}
    info["climb_by_lr"] = {str(lr): round(_median([m["climb"] for m in ms]), 4)
                           for lr, ms in groups.items()}
    info["purity_by_lr"] = {str(lr):
                            round(_median([m["own_final"] for m in ms]), 4)
                            for lr, ms in groups.items()}
    info["anchor_by_lr"] = {str(lr): round(_median([m["anchor"] for m in ms]), 4)
                            for lr, ms in groups.items()}
    n_pts = len(cfg.multipliers) - 1
    for lr, ms in groups.items():
        traj = [_median([m["anchor"] for m in ms])] \
            + [_median([m["shares"][i] for m in ms]) for i in range(n_pts)] \
            + [_median([m["c_final"] for m in ms])]
        if any(prev - nxt > cfg.drop_guard
               for prev, nxt in zip(traj, traj[1:])):
            return info | {"verdict": "review", "reason": "purity_regression",
                           "g2_bar_stable": False}
        climbs = [m["climb"] for m in ms]
        if max(climbs) - min(climbs) >= cfg.disp_guard:
            return info | {"verdict": "review", "reason": "mixed_seeds",
                           "g2_bar_stable": False}
    purities = [_median([m["own_final"] for m in ms])
                for ms in groups.values()]
    canon_climb = _median([m["climb"] for m in groups[CANONICAL_LR]])
    canon_purity = _median([m["own_final"] for m in groups[CANONICAL_LR]])

    def verdict_at(bar: float) -> str:
        if canon_climb >= bar:
            return "purification_universal" \
                if max(purities) - min(purities) <= cfg.conv_band \
                else "partial_purification"
        return "purification_lr_gated" \
            if max(purities) - canon_purity > cfg.conv_band else "review"

    by_bar = {bar: verdict_at(bar) for bar in cfg.climb_bars}
    info["verdict_by_bar"] = {str(b): v for b, v in by_bar.items()}
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    info["f_ext_median_by_lr"] = {
        str(lr): round(_median([m["f_ext"][str(pre_bar_of(lr, cfg))]
                                for m in ms]), 4)
        for lr, ms in groups.items()}
    f_ext_medians = list(info["f_ext_median_by_lr"].values())
    info["f_ext_unified"] = \
        max(f_ext_medians) - min(f_ext_medians) <= cfg.conv_band
    if not info["g2_bar_stable"]:
        return info | {"verdict": "review", "reason": "climb_bar_instability"}
    verdict = by_bar[cfg.climb_bar]
    reason = "unexpected_geometry" if verdict == "review" else ""
    return info | {"verdict": verdict, "reason": reason}


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, ref_canonical: dict, ref_compressed: dict,
                 info: dict, cfg: PurificationConfig | None = None) -> dict:
    cfg = cfg or PurificationConfig()
    refs = reference_map(ref_canonical, ref_compressed)
    rows = []
    for c in cache["cells"]:
        m = cell_metrics(c, refs[(c["lr"], c["seed"])], cfg)
        rows.append({"lr": c["lr"], "seed": c["seed"],
                     "t_gen_ref": c["t_gen_ref"], "anchor": m["anchor"],
                     "c_final": m["c_final"], "own_final": m["own_final"],
                     "climb": m["climb"], "saturated": m["saturated"],
                     "set_match": m["set_match"],
                     "f_ext": m["f_ext"][str(pre_bar_of(c["lr"], cfg))],
                     "t_mem": c["t_mem"], "t_gen": c["t_gen"],
                     "heldout_acc": c["heldout_acc"]})
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_d128_post_grok_3x_horizon",
        "g0_ok": info["g0_ok"], "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "climb_by_lr": info.get("climb_by_lr", {}),
        "purity_by_lr": info.get("purity_by_lr", {}),
        "anchor_by_lr": info.get("anchor_by_lr", {}),
        "f_ext_median_by_lr": info.get("f_ext_median_by_lr", {}),
        "f_ext_unified": info.get("f_ext_unified"),
        "runs": cache.get("runs"), "total_steps": cache.get("total_steps"),
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_ok']} g1={s['g1_complete']} g2={s['g2_bar_stable']}"
             f" runs={s['runs']} total_steps={s['total_steps']}",
             f"anchor_by_lr={s['anchor_by_lr']}",
             f"purity_by_lr={s['purity_by_lr']}"
             f" climb_by_lr={s['climb_by_lr']}",
             f"f_ext_median_by_lr={s['f_ext_median_by_lr']}"
             f" unified={s['f_ext_unified']}"]
    for row in report["cells"]:
        lines.append(f"lr={row['lr']} seed={row['seed']}:"
                     f" anchor={row['anchor']} final={row['c_final']}"
                     f" own={row['own_final']} climb={row['climb']}"
                     f" sat={row['saturated']} set_match={row['set_match']}"
                     f" F_ext={row['f_ext']} heldout={row['heldout_acc']}")
    return lines


def plot_result(cache: dict, ref_canonical: dict, ref_compressed: dict,
                info: dict, path) -> None:
    """One figure: cached-top5 share vs relative time t/t_gen(ref) -- the
    committed pre-grok trajectory faint, the new post-grok segment bold."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path as _Path

    refs = reference_map(ref_canonical, ref_compressed)
    colors = {1e-3: "black", 2e-3: "tab:green", 4e-3: "tab:blue",
              8e-3: "tab:purple"}
    fig, ax = plt.subplots(figsize=(8.5, 5))
    seen = set()
    for c in cache["cells"]:
        ref = refs[(c["lr"], c["seed"])]
        t, col = c["t_gen_ref"], colors[c["lr"]]
        xs_pre = [s["k"] / t for s in ref["snapshots"]] + [ref["steps_run"] / t]
        ys_pre = [s["share"] for s in ref["snapshots"]] + [ref["final_share"]]
        ax.plot(xs_pre, ys_pre, color=col, alpha=0.25, linewidth=1.0)
        xs = [ref["steps_run"] / t] + [s["k"] / t for s in c["snapshots"]] \
            + [c["steps_run"] / t]
        ys = [ref["final_share"]] \
            + [set_share(s["power"], ref["top5"]) for s in c["snapshots"]] \
            + [set_share(c["final_power"], ref["top5"])]
        label = f"lr={c['lr']}" if c["lr"] not in seen else None
        seen.add(c["lr"])
        ax.plot(xs, ys, color=col, linewidth=1.6, marker="o", markersize=3.5,
                label=label)
    ax.axvline(1.0, color="gray", linestyle=":", alpha=0.7)
    ax.set(xlabel="relative time t / t_gen(ref)", xlim=(0, 3.1),
           ylabel="cached-top5 power share C_ref(t)", ylim=(0, 1.02),
           title=f"v1287 post-grok purification: {info['verdict']}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = _Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)
