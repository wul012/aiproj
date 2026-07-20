"""v1284: circuit timing -- does the grokking plateau build the circuit, or wait?

v1283 split the substrate into a coupled phase (train/val rise together, no
memorized plateau) and a delayed/grokking phase; the v1284 P1 probe showed both
end in Fourier frequency circuits (coupled endpoints even MORE concentrated).
This version measures WHEN the final circuit's power arrives relative to
generalization, using deterministic truncated re-runs as weight snapshots
(zero training-code modification, self-verified by a prefix-determinism gate).

Preregistered before any GPU run (see docs/v1284-circuit-timing-brief.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from minigpt.grok_arc_common import agg_pyplot, median as _median, save_figure
from minigpt.grok_checkpoint_v1185 import train_to_grok
from minigpt.grok_delay_gate_v1283 import classify_phase
from minigpt.grok_interp_v1188 import embedding_spectrum, number_embedding
from minigpt.grok_predict_v1186 import evaluate_table
from minigpt.grok_speed_v1279 import scaled_init
from minigpt.grok_v1179 import GrokConfig, make_grok_model

SCHEMA = "grok_circuit_timing_v1284.v1"
VERDICTS = (
    "plateau_is_circuit_construction",
    "construction_is_rapid_in_both",
    "structure_precedes_in_both",
    "coupled_phase_uses_different_solution",
    "review",
)


@dataclass(frozen=True)
class TimingConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    lr: float = 1e-3
    max_steps: int = 60000
    cells: tuple[tuple[int, int, str], ...] = (
        (20, 1337, "coupled"), (20, 1338, "coupled"), (24, 1337, "coupled"),
        (24, 1338, "delayed"), (28, 1337, "delayed"), (28, 1338, "delayed"))
    ladder: tuple[int, ...] = (100, 200, 400, 700, 1000, 1400, 1900,
                               2600, 3400, 4400, 5600)
    top_k: int = 5
    heldout_bar: float = 0.90
    phase_pair: tuple[float, float] = (0.5, 0.7)
    f_low: float = 0.2
    f_high: float = 0.5
    endpoint_min: float = 0.5
    pre_bar: float = 0.1
    pre_bars: tuple[float, ...] = (0.05, 0.1, 0.2)
    max_runs: int = 76
    max_total_steps: int = 260000

    def validate(self) -> None:
        phases = [phase for _w, _s, phase in self.cells]
        if phases.count("coupled") != 3 or phases.count("delayed") != 3:
            raise ValueError("exactly three cells per expected phase")
        if any(w % self.n_head for w, _s, _p in self.cells):
            raise ValueError("every width must be divisible by n_head")
        if list(self.ladder) != sorted(self.ladder) or any(
                k % 100 for k in self.ladder):
            raise ValueError("ladder must be ascending multiples of eval_every")
        if not 0 < self.f_low < self.f_high <= 1:
            raise ValueError("need 0 < f_low < f_high <= 1")
        if self.pre_bar not in self.pre_bars:
            raise ValueError("pre_bar must be on the robustness grid")
        worst = len(self.cells) * (1 + len(self.ladder))
        if worst > self.max_runs:
            raise ValueError("worst-case run count exceeds the budget")


# ------------------------------------------------------------- measurement ----
def _grok_cfg(cfg: TimingConfig, width: int, seed: int, steps: int) -> GrokConfig:
    return GrokConfig(p=cfg.p, train_frac=cfg.train_frac, n_head=cfg.n_head,
                      n_embd=width, max_steps=steps, lr=cfg.lr,
                      seeds=(seed,), wds=(cfg.weight_decay,))


def _power_of(model, p: int) -> list[float]:
    return [float(x) for x in embedding_spectrum(number_embedding(model, p))]


def set_share(power: list[float], freq_set: list[int]) -> float:
    total = sum(power)
    return sum(power[i] for i in freq_set) / total


def train_snapshot(cfg: TimingConfig, width: int, seed: int, steps: int,
                   device) -> dict:
    """One deterministic (possibly truncated) run; returns metrics + spectrum."""
    init = scaled_init(width, seed, 1.0, cfg)
    model, meta, curve = train_to_grok(_grok_cfg(cfg, width, seed, steps),
                                       device, init_state=init)
    last = curve[-1]
    out = {"steps": int(last["step"]), "train_acc": float(last["train_acc"]),
           "val_acc": float(last["val_acc"]),
           "power": _power_of(model, cfg.p)}
    if steps >= cfg.max_steps:  # the full run carries the endpoint extras
        out |= {"t_mem": meta.t_mem, "t_gen": meta.t_gen,
                "heldout_acc": float(evaluate_table(model, meta)["heldout_acc"]),
                "curve": [(int(r["step"]), float(r["train_acc"]),
                           float(r["val_acc"])) for r in curve]}
    return out


def init_share(cfg: TimingConfig, width: int, seed: int,
               freq_set: list[int]) -> float:
    model = make_grok_model(cfg.p + 2, _grok_cfg(cfg, width, seed, 100))
    model.load_state_dict(scaled_init(width, seed, 1.0, cfg))
    return set_share(_power_of(model, cfg.p), freq_set)


# ---------------------------------------------------------------- phase A ----
def run_cell(cfg: TimingConfig, width: int, seed: int, expected: str, device,
             snapshot_fn=train_snapshot) -> dict:
    full = snapshot_fn(cfg, width, seed, cfg.max_steps, device)
    top5 = sorted(range(len(full["power"])),
                  key=lambda i: full["power"][i], reverse=True)[:cfg.top_k]
    curve_by_step = {row[0]: row for row in full["curve"]}
    snapshots, prefix_ok = [], True
    for k in cfg.ladder:
        if k >= full["steps"]:
            break
        snap = snapshot_fn(cfg, width, seed, k, device)
        row = curve_by_step.get(snap["steps"])
        ok = (row is not None
              and abs(row[1] - snap["train_acc"]) < 1e-9
              and abs(row[2] - snap["val_acc"]) < 1e-9)
        prefix_ok = prefix_ok and ok
        snapshots.append({"k": snap["steps"], "train_acc": snap["train_acc"],
                          "val_acc": snap["val_acc"],
                          "share": round(set_share(snap["power"], top5), 6),
                          "prefix_ok": ok})
    return {"width": width, "seed": seed, "expected_phase": expected,
            "steps_run": full["steps"], "t_mem": full["t_mem"],
            "t_gen": full["t_gen"], "heldout_acc": full["heldout_acc"],
            "curve": full["curve"], "top5": top5,
            "final_share": round(set_share(full["power"], top5), 6),
            "c0_share": round(init_share(cfg, width, seed, top5), 6),
            "prefix_ok": prefix_ok, "snapshots": snapshots}


def run_phase_a(cfg: TimingConfig, device, snapshot_fn=train_snapshot,
                preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["width"], c["seed"]): dict(c) for c in preloaded}
    cells, runs, steps = [], 0, 0
    for width, seed, expected in cfg.cells:
        cell = done.get((width, seed)) or \
            run_cell(cfg, width, seed, expected, device, snapshot_fn)
        cell["expected_phase"] = expected
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
def structure_fraction(cell: dict, bar: float) -> float:
    pre = [s for s in cell["snapshots"] if s["val_acc"] <= bar]
    if not pre:
        return 0.0
    share = pre[-1]["share"]
    denom = cell["final_share"] - cell["c0_share"]
    if denom <= 0:
        return 0.0
    return min(1.0, max(0.0, (share - cell["c0_share"]) / denom))


def _g0(cache: dict, cfg: TimingConfig) -> str:
    for cell in cache["cells"]:
        if not cell["prefix_ok"]:
            return "prefix_nondeterministic"
        if cell["heldout_acc"] < cfg.heldout_bar:
            return "substrate_unsound"
        if classify_phase(cell, cfg.phase_pair, cfg) != cell["expected_phase"]:
            return "phase_mismatch"
    return ""


def _g1(cache: dict, cfg: TimingConfig) -> bool:
    if len(cache["cells"]) != len(cfg.cells):
        return False
    for cell in cache["cells"]:
        expected = [k for k in cfg.ladder if k < cell["steps_run"]]
        if [s["k"] for s in cell["snapshots"]] != expected:
            return False
    return True


def _verdict_at_bar(cache: dict, cfg: TimingConfig, bar: float) -> str:
    by_phase = {"coupled": [], "delayed": []}
    for cell in cache["cells"]:
        by_phase[cell["expected_phase"]].append(structure_fraction(cell, bar))
    f_coup = _median(by_phase["coupled"])
    f_del = _median(by_phase["delayed"])
    if f_del >= cfg.f_high and f_coup <= cfg.f_low:
        return "plateau_is_circuit_construction"
    if f_del <= cfg.f_low and f_coup <= cfg.f_low:
        return "construction_is_rapid_in_both"
    if f_del >= cfg.f_high and f_coup >= cfg.f_high:
        return "structure_precedes_in_both"
    return "review"


def decide(cache: dict, cfg: TimingConfig | None = None) -> dict:
    cfg = cfg or TimingConfig()
    cfg.validate()
    g0_reason = _g0(cache, cfg)
    info: dict = {"g0_ok": g0_reason == "", "g1_complete": _g1(cache, cfg)}
    if g0_reason:
        return info | {"verdict": "review", "reason": g0_reason,
                       "g2_bar_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_bar_stable": False}
    coupled_finals = [c["final_share"] for c in cache["cells"]
                      if c["expected_phase"] == "coupled"]
    info["coupled_final_median"] = round(_median(coupled_finals), 4)
    info["fractions"] = {f"{c['width']}/{c['seed']}":
                         round(structure_fraction(c, cfg.pre_bar), 4)
                         for c in cache["cells"]}
    if info["coupled_final_median"] < cfg.endpoint_min:
        return info | {"verdict": "coupled_phase_uses_different_solution",
                       "reason": "", "g2_bar_stable": True}
    by_bar = {bar: _verdict_at_bar(cache, cfg, bar) for bar in cfg.pre_bars}
    info["verdict_by_bar"] = by_bar
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    if info["g2_bar_stable"]:
        verdict = by_bar[cfg.pre_bar]
        info |= {"verdict": verdict,
                 "reason": "mixed_fractions" if verdict == "review" else ""}
    else:
        info |= {"verdict": "review", "reason": "bar_instability"}
    return info


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, info: dict,
                 cfg: TimingConfig | None = None) -> dict:
    cfg = cfg or TimingConfig()
    rows = []
    for c in cache["cells"]:
        rows.append({"width": c["width"], "seed": c["seed"],
                     "phase": c["expected_phase"],
                     "fraction": round(structure_fraction(c, cfg.pre_bar), 4),
                     "c0_share": c["c0_share"], "final_share": c["final_share"],
                     "t_mem": c["t_mem"], "t_gen": c["t_gen"],
                     "heldout_acc": c["heldout_acc"],
                     "snapshot_count": len(c["snapshots"])})
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_canonical_recipe_6_cells",
        "g0_ok": info["g0_ok"], "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "fractions": info.get("fractions", {}),
        "coupled_final_median": info.get("coupled_final_median"),
        "runs": cache.get("runs"), "total_steps": cache.get("total_steps"),
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_ok']} g1={s['g1_complete']} g2={s['g2_bar_stable']}"
             f" runs={s['runs']} total_steps={s['total_steps']}",
             f"coupled_final_median={s['coupled_final_median']}"]
    for key, frac in s["fractions"].items():
        lines.append(f"cell {key}: F={frac}")
    for row in report["cells"]:
        lines.append(f"w={row['width']} seed={row['seed']} ({row['phase']}):"
                     f" F={row['fraction']} c0={row['c0_share']}"
                     f" final={row['final_share']} t_mem={row['t_mem']}"
                     f" t_gen={row['t_gen']} heldout={row['heldout_acc']}")
    return lines


def plot_result(cache: dict, info: dict, path) -> None:
    """One figure: C(t) trajectories, coupled green vs delayed blue,
    val curves faint, the w=24 cross-phase pair emphasized."""
    plt = agg_pyplot()

    fig, ax = plt.subplots(figsize=(8.5, 5))
    for c in cache["cells"]:
        color = "tab:green" if c["expected_phase"] == "coupled" else "tab:blue"
        lw = 2.4 if c["width"] == 24 else 1.2
        xs = [s["k"] for s in c["snapshots"]] + [c["steps_run"]]
        ys = [s["share"] for s in c["snapshots"]] + [c["final_share"]]
        ax.plot(xs, ys, color=color, linewidth=lw, marker="o", markersize=3,
                label=f"w={c['width']}/{c['seed']} ({c['expected_phase']})")
        ax.plot([r[0] for r in c["curve"]], [r[2] for r in c["curve"]],
                color=color, alpha=0.18, linewidth=0.8)
    ax.set(xscale="log", xlabel="training step (log)",
           ylabel="final-circuit power share C(t)  /  val acc (faint)",
           ylim=(0, 1.02),
           title=f"v1284 circuit timing: {info['verdict']}")
    ax.legend(fontsize=6.5, ncol=2)
    fig.tight_layout()
    save_figure(fig, path)
