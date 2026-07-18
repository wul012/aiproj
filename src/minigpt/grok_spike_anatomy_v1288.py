"""v1288: spike anatomy -- is weight decay the post-grok destabilizer?

v1287 found grokked solutions are metastable under continued training:
whole-solution train+val spikes that self-heal in 100-300 steps (two cells
censored mid-spike at their horizons). This version branches nine spike-prone
cells at verified-healthy committed snapshot steps into paired continuation
arms -- wd=1.0 vs wd=0.0, sharing the optimizer-reset confound -- and counts
spike episodes per arm; two cheap un-censoring re-runs extend the v1287 dead
cells 1,000 steps past their horizons. Branch integrity is gated on bit-exact
reproduction of the committed v1287 curves; endpoint heldout is deliberately
NOT a gate (an arm may end mid-spike -- that is data). Secondary, non-verdict:
the purity-freeze prediction (wd=0 arm purity frozen, wd=1 climbing) tying
purification and metastability to one wd mechanism.

Preregistered before any GPU run (see docs/v1288-spike-anatomy-brief.md).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone

from minigpt.grok_checkpoint_v1185 import train_to_grok
from minigpt.grok_circuit_timing_v1284 import set_share
from minigpt.grok_interp_v1188 import embedding_spectrum, number_embedding
from minigpt.grok_predict_v1186 import evaluate_table
from minigpt.grok_purification_v1287 import top_freqs
from minigpt.grok_speed_v1279 import scaled_init, total_norm_of
from minigpt.grok_v1179 import GrokConfig

SCHEMA = "grok_spike_anatomy_v1288.v1"
VERDICTS = ("spikes_are_wd_driven", "spikes_persist_without_wd",
            "spikes_need_optimizer_history", "review")
ARM_KEYS = ("wd1", "wd0")


@dataclass(frozen=True)
class SpikeAnatomyConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0  # substrate recipe = the wd=1.0 arm
    n_head: int = 4
    width: int = 128
    lr: float = 1e-3           # placeholder; every cell overrides via replace
    cells: tuple[tuple[float, int, int, int], ...] = (
        (1e-3, 1339, 14700, 31500),
        (2e-3, 1337, 2700, 5700), (2e-3, 1338, 3900, 8400),
        (4e-3, 1337, 2000, 4200), (4e-3, 1338, 2500, 5400),
        (4e-3, 1339, 1400, 3000),
        (8e-3, 1337, 1400, 3000), (8e-3, 1338, 2500, 4200),
        (8e-3, 1339, 2100, 4500))
    uncensor: tuple[tuple[float, int, int], ...] = (
        (4e-3, 1338, 6400), (4e-3, 1339, 4000))
    arm_wds: tuple[float, float] = (1.0, 0.0)
    top_k: int = 5
    spike_bar: float = 0.9
    spike_bars: tuple[float, ...] = (0.8, 0.85, 0.9)
    branch_bar: float = 0.9
    s1_bar: int = 5
    s0_persist: int = 3
    episode_max_steps: int = 500
    grok_stop_val: float = 2.0  # above 1.0 = early stop can never fire
    eval_every: int = 100
    max_runs: int = 32
    max_total_steps: int = 130000

    def validate(self) -> None:
        if self.width % self.n_head:
            raise ValueError("width must be divisible by n_head")
        if self.grok_stop_val <= 1.0:
            raise ValueError("grok_stop_val must exceed 1.0 (no early stop)")
        if self.spike_bar not in self.spike_bars:
            raise ValueError("spike_bar must be on the robustness grid")
        if not 0 < self.s1_bar <= len(self.cells):
            raise ValueError("s1_bar must be within the cell count")
        if tuple(sorted(self.arm_wds, reverse=True)) != self.arm_wds \
                or len(self.arm_wds) != 2 or self.arm_wds[1] != 0.0:
            raise ValueError("arms must be (substrate wd, 0.0)")
        steps = 0
        for _lr, _seed, k_branch, horizon in self.cells:
            if k_branch % self.eval_every or horizon % self.eval_every \
                    or not 0 < k_branch < horizon:
                raise ValueError("branch points must be eval-aligned and "
                                 "inside the horizon")
            steps += k_branch + 2 * (horizon - k_branch)
        for _lr, _seed, ext in self.uncensor:
            if ext % self.eval_every or ext <= 0:
                raise ValueError("uncensor horizons must be eval multiples")
            steps += ext
        if 3 * len(self.cells) + len(self.uncensor) > self.max_runs:
            raise ValueError("run count exceeds the budget")
        if steps > self.max_total_steps:
            raise ValueError("total step count exceeds the budget")


def arm_key(wd: float) -> str:
    return "wd1" if wd else "wd0"


# ------------------------------------------------------------- measurement ----
def _grok_cfg(cfg: SpikeAnatomyConfig, seed: int, steps: int,
              wd: float) -> GrokConfig:
    return GrokConfig(p=cfg.p, train_frac=cfg.train_frac, n_head=cfg.n_head,
                      n_embd=cfg.width, max_steps=steps, lr=cfg.lr,
                      grok_stop_val=cfg.grok_stop_val,
                      seeds=(seed,), wds=(wd,))


def _rows(curve: list[dict]) -> list[tuple[int, float, float]]:
    return [(int(r["step"]), float(r["train_acc"]), float(r["val_acc"]))
            for r in curve]


def _spectrum_norm(model, p: int) -> tuple[list[float], float]:
    power = [float(x) for x in embedding_spectrum(number_embedding(model, p))]
    return power, total_norm_of(model.state_dict())


def branch_run(cfg: SpikeAnatomyConfig, lr: float, seed: int, k_branch: int,
               device) -> dict:
    """Deterministic re-run to the branch point; returns state + measurements."""
    cell_cfg = replace(cfg, lr=lr)
    init = scaled_init(cfg.width, seed, 1.0, cell_cfg)
    model, _meta, curve = train_to_grok(
        _grok_cfg(cell_cfg, seed, k_branch, cfg.weight_decay), device,
        init_state=init)
    power, norm = _spectrum_norm(model, cfg.p)
    state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    return {"state": state, "curve": _rows(curve), "power": power,
            "norm": norm}


def arm_run(cfg: SpikeAnatomyConfig, lr: float, seed: int, state: dict,
            steps: int, wd: float, device) -> dict:
    """Continue from the branch state with a fresh optimizer and the arm wd."""
    cell_cfg = replace(cfg, lr=lr)
    model, meta, curve = train_to_grok(
        _grok_cfg(cell_cfg, seed, steps, wd), device, init_state=state)
    power, norm = _spectrum_norm(model, cfg.p)
    heldout = float(evaluate_table(model, meta)["heldout_acc"])
    return {"wd": wd, "curve": _rows(curve), "power": power, "norm": norm,
            "heldout_acc": heldout}


def uncensor_run(cfg: SpikeAnatomyConfig, lr: float, seed: int, ext: int,
                 device) -> dict:
    """Full re-run of a v1287 dead cell extended past its old horizon."""
    cell_cfg = replace(cfg, lr=lr)
    init = scaled_init(cfg.width, seed, 1.0, cell_cfg)
    model, meta, curve = train_to_grok(
        _grok_cfg(cell_cfg, seed, ext, cfg.weight_decay), device,
        init_state=init)
    heldout = float(evaluate_table(model, meta)["heldout_acc"])
    return {"lr": lr, "seed": seed, "ext_horizon": ext, "curve": _rows(curve),
            "heldout_acc": heldout}


# ---------------------------------------------------------------- phase A ----
def run_cell(cfg: SpikeAnatomyConfig, lr: float, seed: int, k_branch: int,
             horizon: int, device, branch_fn=branch_run,
             arm_fn=arm_run) -> dict:
    branch = branch_fn(cfg, lr, seed, k_branch, device)
    last = branch["curve"][-1]
    arms = {arm_key(wd): arm_fn(cfg, lr, seed, branch["state"],
                                horizon - k_branch, wd, device)
            for wd in cfg.arm_wds}
    return {"lr": lr, "seed": seed, "k_branch": k_branch, "horizon": horizon,
            "branch_curve": branch["curve"], "branch_train": last[1],
            "branch_val": last[2], "branch_power": branch["power"],
            "branch_norm": branch["norm"], "arms": arms}


def run_phase_a(cfg: SpikeAnatomyConfig, device, branch_fn=branch_run,
                arm_fn=arm_run, uncensor_fn=uncensor_run,
                preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["lr"], c["seed"]): dict(c) for c in preloaded}
    cells, runs, steps = [], 0, 0
    for lr, seed, k_branch, horizon in cfg.cells:
        cell = done.get((lr, seed)) or \
            run_cell(cfg, lr, seed, k_branch, horizon, device, branch_fn,
                     arm_fn)
        runs += 3
        steps += k_branch + 2 * (horizon - k_branch)
        if runs > cfg.max_runs or steps > cfg.max_total_steps:
            raise RuntimeError("trajectory budget exceeded")
        cells.append(cell)
    extensions = []
    for lr, seed, ext in cfg.uncensor:
        extensions.append(uncensor_fn(cfg, lr, seed, ext, device))
        runs += 1
        steps += ext
        if runs > cfg.max_runs or steps > cfg.max_total_steps:
            raise RuntimeError("trajectory budget exceeded")
    return {"schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": asdict(cfg), "cells": cells, "uncensor": extensions,
            "runs": runs, "total_steps": steps}


# ----------------------------------------------------------------- decide ----
def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def episodes(curve: list, bar: float, eval_every: int = 100) -> list[dict]:
    """Maximal runs of val < bar: the spike episodes of one trajectory."""
    eps: list[dict] = []
    cur: dict | None = None
    for step, _train, val in curve:
        if val < bar:
            if cur is None:
                cur = {"start": int(step), "min_val": float(val)}
            cur["end"] = int(step)
            cur["min_val"] = min(cur["min_val"], float(val))
        elif cur is not None:
            cur["censored"] = False
            eps.append(cur)
            cur = None
    if cur is not None:
        cur["censored"] = True
        eps.append(cur)
    for ep in eps:
        ep["duration"] = ep["end"] - ep["start"] + eval_every
    return eps


def window_episodes(ref_cell: dict, k_branch: int, horizon: int,
                    bar: float) -> list[dict]:
    """Continuous-run episodes inside the branch window, from the v1287 cache."""
    rows = [r for r in ref_cell["curve"] if k_branch < r[0] <= horizon]
    return episodes(rows, bar)


def own_share(power: list[float], k: int) -> float:
    return set_share(power, top_freqs(power, k))


def _g0(cache: dict, ref: dict, cfg: SpikeAnatomyConfig) -> str:
    refs = {(c["lr"], c["seed"]): c for c in ref["cells"]}
    for cell in cache["cells"]:
        rc = refs.get((cell["lr"], cell["seed"]))
        if rc is None:
            return "reference_mismatch"
        by_step = {r[0]: r for r in rc["curve"]}
        for step, train, val in cell["branch_curve"]:
            row = by_step.get(int(step))
            if row is None or abs(row[1] - train) > 1e-9 \
                    or abs(row[2] - val) > 1e-9:
                return "reference_mismatch"
        if cell["branch_val"] < cfg.branch_bar:
            return "branch_unhealthy"
    for ext in cache["uncensor"]:
        rc = refs.get((ext["lr"], ext["seed"]))
        if rc is None:
            return "reference_mismatch"
        by_step = {r[0]: r for r in ext["curve"]}
        for step, train, val in rc["curve"]:
            row = by_step.get(int(step))
            if row is None or abs(row[1] - train) > 1e-9 \
                    or abs(row[2] - val) > 1e-9:
                return "reference_mismatch"
    return ""


def _g1(cache: dict, cfg: SpikeAnatomyConfig) -> bool:
    if len(cache["cells"]) != len(cfg.cells) \
            or len(cache["uncensor"]) != len(cfg.uncensor):
        return False
    for cell, (lr, seed, k_branch, horizon) in zip(cache["cells"], cfg.cells):
        if (cell["lr"], cell["seed"]) != (lr, seed):
            return False
        for key in ARM_KEYS:
            arm = cell["arms"].get(key)
            if arm is None or arm["curve"][-1][0] != horizon - k_branch:
                return False
    for ext, (lr, seed, steps) in zip(cache["uncensor"], cfg.uncensor):
        if (ext["lr"], ext["seed"]) != (lr, seed) \
                or ext["curve"][-1][0] != steps:
            return False
    return True


def _counts(cache: dict, bar: float) -> tuple[int, int]:
    s1 = sum(1 for c in cache["cells"]
             if episodes(c["arms"]["wd1"]["curve"], bar))
    s0 = sum(1 for c in cache["cells"]
             if episodes(c["arms"]["wd0"]["curve"], bar))
    return s1, s0


def decide(cache: dict, ref: dict,
           cfg: SpikeAnatomyConfig | None = None) -> dict:
    cfg = cfg or SpikeAnatomyConfig()
    cfg.validate()
    g0_reason = _g0(cache, ref, cfg)
    info: dict = {"g0_ok": g0_reason == "", "g1_complete": _g1(cache, cfg)}
    if g0_reason:
        return info | {"verdict": "review", "reason": g0_reason,
                       "g2_bar_stable": False}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g2_bar_stable": False}
    refs = {(c["lr"], c["seed"]): c for c in ref["cells"]}
    spikes_by_cell = {}
    for c in cache["cells"]:
        rc = refs[(c["lr"], c["seed"])]
        spikes_by_cell[f"{c['lr']}/{c['seed']}"] = {
            "wd1": len(episodes(c["arms"]["wd1"]["curve"], cfg.spike_bar)),
            "wd0": len(episodes(c["arms"]["wd0"]["curve"], cfg.spike_bar)),
            "continuous": len(window_episodes(rc, c["k_branch"], c["horizon"],
                                              cfg.spike_bar))}
    info["spikes_by_cell"] = spikes_by_cell
    for c in cache["cells"]:
        for key in ARM_KEYS:
            for ep in episodes(c["arms"][key]["curve"], cfg.spike_bar):
                if not ep["censored"] \
                        and ep["duration"] > cfg.episode_max_steps:
                    return info | {"verdict": "review",
                                   "reason": "atypical_morphology",
                                   "g2_bar_stable": False}

    def verdict_at(bar: float) -> str:
        s1, s0 = _counts(cache, bar)
        if s1 >= cfg.s1_bar and s0 == 0:
            return "spikes_are_wd_driven"
        if s0 >= cfg.s0_persist:
            return "spikes_persist_without_wd"
        if s1 == 0 and s0 == 0:
            return "spikes_need_optimizer_history"
        return "review"

    s1, s0 = _counts(cache, cfg.spike_bar)
    info |= {"s1": s1, "s0": s0}
    by_bar = {bar: verdict_at(bar) for bar in cfg.spike_bars}
    info["verdict_by_bar"] = {str(b): v for b, v in by_bar.items()}
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    for key in ARM_KEYS:
        deltas = [own_share(c["arms"][key]["power"], cfg.top_k)
                  - own_share(c["branch_power"], cfg.top_k)
                  for c in cache["cells"]]
        info[f"purity_delta_{key}"] = round(_median(deltas), 4)
        norms = [c["arms"][key]["norm"] / c["branch_norm"]
                 for c in cache["cells"]]
        info[f"norm_ratio_{key}"] = round(_median(norms), 4)
    info["uncensor"] = [
        {"lr": e["lr"], "seed": e["seed"],
         "recovered": e["curve"][-1][2] >= cfg.branch_bar,
         "final_val": e["curve"][-1][2], "heldout_acc": e["heldout_acc"]}
        for e in cache["uncensor"]]
    if not info["g2_bar_stable"]:
        return info | {"verdict": "review", "reason": "spike_bar_instability"}
    verdict = by_bar[cfg.spike_bar]
    reason = ""
    if verdict == "review":
        reason = "unexpected_geometry" if s1 == 0 and s0 > 0 \
            else "mixed_evidence"
    return info | {"verdict": verdict, "reason": reason}


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, ref: dict, info: dict,
                 cfg: SpikeAnatomyConfig | None = None) -> dict:
    cfg = cfg or SpikeAnatomyConfig()
    rows = []
    for c in cache["cells"]:
        key = f"{c['lr']}/{c['seed']}"
        spikes = info.get("spikes_by_cell", {}).get(key, {})
        row = {"lr": c["lr"], "seed": c["seed"], "k_branch": c["k_branch"],
               "horizon": c["horizon"], "branch_val": c["branch_val"],
               "spikes_wd1": spikes.get("wd1"),
               "spikes_wd0": spikes.get("wd0"),
               "spikes_continuous": spikes.get("continuous"),
               "branch_purity": round(own_share(c["branch_power"], cfg.top_k),
                                      6)}
        for arm in ARM_KEYS:
            a = c["arms"][arm]
            row |= {f"purity_{arm}": round(own_share(a["power"], cfg.top_k), 6),
                    f"min_val_{arm}": round(min(r[2] for r in a["curve"]), 6),
                    f"ends_in_spike_{arm}": a["curve"][-1][2] < cfg.spike_bar}
        rows.append(row)
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "scope": "own_grokked_substrate_toy_scale_d128_branch_arms",
        "g0_ok": info["g0_ok"], "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "s1": info.get("s1"), "s0": info.get("s0"),
        "s1_bar": cfg.s1_bar, "s0_persist": cfg.s0_persist,
        "purity_delta_wd1": info.get("purity_delta_wd1"),
        "purity_delta_wd0": info.get("purity_delta_wd0"),
        "norm_ratio_wd1": info.get("norm_ratio_wd1"),
        "norm_ratio_wd0": info.get("norm_ratio_wd0"),
        "uncensor": info.get("uncensor", []),
        "runs": cache.get("runs"), "total_steps": cache.get("total_steps"),
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "cells": rows}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']} scope={s['scope']}",
             f"g0={s['g0_ok']} g1={s['g1_complete']} g2={s['g2_bar_stable']}"
             f" runs={s['runs']} total_steps={s['total_steps']}",
             f"S1={s['s1']} (bar {s['s1_bar']}) S0={s['s0']}"
             f" (persist bar {s['s0_persist']})",
             f"purity_delta wd1={s['purity_delta_wd1']}"
             f" wd0={s['purity_delta_wd0']}"
             f" norm_ratio wd1={s['norm_ratio_wd1']}"
             f" wd0={s['norm_ratio_wd0']}"]
    for e in s["uncensor"]:
        lines.append(f"uncensor lr={e['lr']} seed={e['seed']}:"
                     f" recovered={e['recovered']}"
                     f" final_val={e['final_val']}"
                     f" heldout={e['heldout_acc']}")
    for row in report["cells"]:
        lines.append(
            f"lr={row['lr']} seed={row['seed']}: spikes"
            f" wd1={row['spikes_wd1']} wd0={row['spikes_wd0']}"
            f" cont={row['spikes_continuous']}"
            f" min_val wd1={row['min_val_wd1']} wd0={row['min_val_wd0']}"
            f" purity {row['branch_purity']}->"
            f"{row['purity_wd1']}/{row['purity_wd0']}")
    return lines


def plot_result(cache: dict, info: dict, path) -> None:
    """One file, two panels: (a) paired arm val trajectories on normalized
    time (wd=1 solid, wd=0 dashed), (b) the un-censor runs crossing the old
    v1287 horizon."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path as _Path

    colors = {1e-3: "black", 2e-3: "tab:green", 4e-3: "tab:blue",
              8e-3: "tab:purple"}
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.6),
                                 gridspec_kw={"width_ratios": [3, 2]})
    seen = set()
    for c in cache["cells"]:
        col = colors[c["lr"]]
        for key, style in (("wd1", "-"), ("wd0", "--")):
            arm = c["arms"][key]
            xs = [(c["k_branch"] + r[0]) / c["horizon"] for r in arm["curve"]]
            ys = [r[2] for r in arm["curve"]]
            label = f"lr={c['lr']} {key}" if (c["lr"], key) not in seen \
                else None
            seen.add((c["lr"], key))
            ax.plot(xs, ys, style, color=col, linewidth=1.1, alpha=0.75,
                    label=label)
    ax.set(xlabel="t / horizon", ylabel="val acc", ylim=(0, 1.05),
           title=f"branch arms: {info['verdict']}")
    ax.legend(fontsize=6, ncol=2)
    for e in cache["uncensor"]:
        old = e["ext_horizon"] - 1000
        xs = [r[0] / old for r in e["curve"]]
        ys = [r[2] for r in e["curve"]]
        bx.plot(xs, ys, color="tab:blue", linewidth=1.3,
                label=f"lr={e['lr']} seed={e['seed']}")
    bx.axvline(1.0, color="gray", linestyle=":", alpha=0.8)
    bx.set(xlabel="t / old horizon", ylabel="val acc", ylim=(0, 1.05),
           title="un-censoring the v1287 deaths")
    bx.legend(fontsize=7)
    fig.tight_layout()
    out = _Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)
