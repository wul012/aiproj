"""v1289: spike microscopy -- does the collapse tear the circuit?

v1287 found grokked solutions are metastable (train+val spikes that
self-heal); v1288 proved the spikes are wd-driven. Both saw spikes only at
100-step eval resolution -- the deep events collapse AND mostly recover
between evals. v1289 re-runs the nine spiking committed v1287 trajectories
deterministically (same Adam moments -- a faithful line-for-line
reimplementation of the train_to_grok loop, certified by bit-equality of
every coarse row against the committed cache) and records per-step dense
measurements inside preregistered windows around every committed post-grok
episode: val/train accuracy, the full embedding power spectrum, total
weight norm, and the training backward's own loss and gradient norm.

Primary question: during a deep collapse (dense min val < 0.5), does the
number-embedding Fourier circuit collapse too? Statistic per qualified
episode: r = min in-episode top-5 share / baseline share (5-step median
smoothed, top-5 set frozen from the episode's own baseline). Trigger-style
readouts (loss precursor lead, gradient shove size, norm trace) are
preregistered secondaries, non-verdict by the v1286 bar-instability lesson.

Preregistered before any GPU run (see docs/v1289-spike-microscopy-brief.md).
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone

import torch

from minigpt.grok_arc_common import agg_pyplot, median as _median, save_figure
from minigpt.grok_circuit_timing_v1284 import set_share
from minigpt.grok_interp_v1188 import embedding_spectrum, number_embedding
from minigpt.grok_purification_v1287 import top_freqs
from minigpt.grok_speed_v1279 import scaled_init, total_norm_of
from minigpt.grok_spike_anatomy_v1288 import episodes
from minigpt.grok_v1179 import (
    GrokConfig,
    answer_accuracy,
    answer_loss,
    build_modular_task,
    make_grok_model,
    split_indices,
)
from minigpt.script_runtime import seed_everything

SCHEMA = "grok_spike_microscopy_v1289.v1"
VERDICTS = ("spike_preserves_circuit", "spike_destroys_circuit",
            "spike_mixed", "review")


@dataclass(frozen=True)
class SpikeMicroscopyConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0  # the committed substrate recipe
    n_head: int = 4
    width: int = 128
    lr: float = 1e-3           # placeholder; every cell overrides via replace
    # (lr, seed, rerun_end, dense windows); windows derived mechanically from
    # the committed v1287 episode census (P1), merged where overlapping.
    cells: tuple[tuple[float, int, int, tuple[tuple[int, int], ...]], ...] = (
        (1e-3, 1338, 14000, ((13200, 14000),)),
        (1e-3, 1339, 25700, ((10900, 11700), (12300, 13000),
                             (16900, 17600), (25000, 25700))),
        (2e-3, 1337, 5500, ((2200, 2900), (4800, 5500))),
        (2e-3, 1338, 8400, ((6200, 6900), (7000, 7700), (7900, 8400))),
        (4e-3, 1337, 3700, ((1300, 2000), (2600, 3700))),
        (4e-3, 1338, 5400, ((1500, 2200), (3400, 4100), (4300, 5400))),
        (4e-3, 1339, 3000, ((900, 1600), (2100, 3000))),
        (8e-3, 1338, 3500, ((1100, 2300), (2800, 3500))),
        (8e-3, 1339, 4500, ((3700, 4500),)))
    top_k: int = 5
    spike_bar: float = 0.9
    deep_bar: float = 0.5
    deep_bars: tuple[float, ...] = (0.5, 0.55, 0.6)
    preserve_bar: float = 0.8
    destroy_bar: float = 0.5
    baseline_steps: int = 100
    min_baseline: int = 30
    smooth_window: int = 5
    min_deep: int = 3
    loss_break_mads: float = 20.0
    loss_break_sustain: int = 5
    grok_stop_val: float = 2.0  # above 1.0 = early stop can never fire
    eval_every: int = 100
    max_runs: int = 10
    max_total_steps: int = 75000
    max_dense_steps: int = 16000

    def validate(self) -> None:
        if self.width % self.n_head:
            raise ValueError("width must be divisible by n_head")
        if self.grok_stop_val <= 1.0:
            raise ValueError("grok_stop_val must exceed 1.0 (no early stop)")
        if self.deep_bar not in self.deep_bars:
            raise ValueError("deep_bar must be on the robustness grid")
        if not 0 < self.destroy_bar < self.preserve_bar:
            raise ValueError("label bars must satisfy 0 < destroy < preserve")
        if self.smooth_window < 1 or self.smooth_window % 2 == 0:
            raise ValueError("smooth_window must be odd and positive")
        if not 0 < self.min_baseline <= self.baseline_steps:
            raise ValueError("min_baseline must be within baseline_steps")
        steps = dense = 0
        for _lr, _seed, rerun_end, windows in self.cells:
            if not windows or windows[-1][1] != rerun_end:
                raise ValueError("rerun_end must equal the last window end")
            prev_end = -1
            for w0, w1 in windows:
                if w0 % self.eval_every or w1 % self.eval_every \
                        or not 0 <= w0 < w1 or w0 <= prev_end:
                    raise ValueError("windows must be eval-aligned, ordered "
                                     "and non-overlapping")
                prev_end = w1
                dense += w1 - w0 + 1
            steps += rerun_end
        if len(self.cells) > self.max_runs:
            raise ValueError("run count exceeds the budget")
        if steps > self.max_total_steps:
            raise ValueError("total step count exceeds the budget")
        if dense > self.max_dense_steps:
            raise ValueError("dense step count exceeds the budget")


# ------------------------------------------------------------- measurement ----
def _window_of(step: int, windows: tuple) -> tuple[int, int] | None:
    for w0, w1 in windows:
        if w0 <= step <= w1:
            return (w0, w1)
    return None


def dense_run(cfg: SpikeMicroscopyConfig, lr: float, seed: int,
              rerun_end: int, windows: tuple, device) -> dict:
    """One faithful re-run of the committed trajectory with dense in-window
    measurement. Mirrors train_to_grok line-for-line (same init, same seeding,
    same eval-then-update order, same rounding); every added measurement is a
    pure read, so the coarse rows must reproduce the committed curve bit-equal
    -- decide() gates on exactly that."""
    cell_cfg = replace(cfg, lr=lr)
    init = scaled_init(cfg.width, seed, 1.0, cell_cfg)
    gcfg = GrokConfig(p=cfg.p, train_frac=cfg.train_frac, n_head=cfg.n_head,
                      n_embd=cfg.width, max_steps=rerun_end, lr=lr,
                      grok_stop_val=cfg.grok_stop_val,
                      seeds=(seed,), wds=(cfg.weight_decay,))
    vocab_size = gcfg.p + 2
    full_data = build_modular_task(gcfg.p)
    seed_everything(seed)
    train_idx, val_idx = split_indices(full_data.shape[0], gcfg.train_frac,
                                       seed)
    model = make_grok_model(vocab_size, gcfg).to(device)
    model.load_state_dict(init)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=gcfg.lr, betas=(gcfg.beta1, gcfg.beta2),
        weight_decay=cfg.weight_decay)
    train = full_data.index_select(0, train_idx).to(device)
    val = full_data.index_select(0, val_idx).to(device)

    coarse: list[tuple[int, float, float]] = []
    dense = {w: {"w0": w[0], "w1": w[1], "steps": [], "train_acc": [],
                 "val_acc": [], "train_loss": [], "grad_norm": [],
                 "norm": [], "power": []} for w in windows}
    step = 0
    while True:
        at_coarse = step % gcfg.eval_every == 0 or step == gcfg.max_steps
        win = _window_of(step, windows)
        if at_coarse or win is not None:
            train_acc = answer_accuracy(model, train)
            val_acc = answer_accuracy(model, val)
        if at_coarse:
            coarse.append((step, round(train_acc, 6), round(val_acc, 6)))
        block = dense[win] if win is not None else None
        if block is not None:
            block["steps"].append(step)
            block["train_acc"].append(float(train_acc))
            block["val_acc"].append(float(val_acc))
            block["norm"].append(total_norm_of(model.state_dict()))
            block["power"].append([
                float(x) for x in
                embedding_spectrum(number_embedding(model, cfg.p))])
        if step >= gcfg.max_steps:
            if block is not None:  # no update at the horizon step
                block["train_loss"].append(None)
                block["grad_norm"].append(None)
            break
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = answer_loss(model, train)
        loss.backward()
        if block is not None:
            block["train_loss"].append(float(loss.item()))
            with torch.no_grad():
                block["grad_norm"].append(float(torch.sqrt(sum(
                    (p.grad.float() ** 2).sum()
                    for p in model.parameters() if p.grad is not None))))
        optimizer.step()
        step += 1
    packed = []
    for w in windows:
        block = dense[w]
        block["power"] = torch.tensor(block["power"], dtype=torch.float32)
        packed.append(block)
    return {"lr": lr, "seed": seed, "rerun_end": rerun_end,
            "windows": [list(w) for w in windows], "coarse": coarse,
            "dense": packed}


# ---------------------------------------------------------------- phase A ----
def run_phase_a(cfg: SpikeMicroscopyConfig, device, dense_fn=dense_run,
                preloaded: tuple = ()) -> dict:
    cfg.validate()
    done = {(c["lr"], c["seed"]): dict(c) for c in preloaded}
    cells, runs, steps = [], 0, 0
    for lr, seed, rerun_end, windows in cfg.cells:
        cell = done.get((lr, seed)) or \
            dense_fn(cfg, lr, seed, rerun_end, windows, device)
        runs += 1
        steps += rerun_end
        if runs > cfg.max_runs or steps > cfg.max_total_steps:
            raise RuntimeError("trajectory budget exceeded")
        cells.append(cell)
    return {"schema": SCHEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "config": asdict(cfg), "cells": cells,
            "runs": runs, "total_steps": steps}


# ----------------------------------------------------------------- analysis ----
def _smooth(xs: list[float], w: int) -> list[float]:
    half = w // 2
    return [_median(xs[max(0, i - half): i + half + 1])
            for i in range(len(xs))]


def window_power(block, i: int) -> list[float]:
    row = block["power"][i]
    return [float(x) for x in row]


def dense_episodes(block: dict, bar: float) -> list[dict]:
    triples = list(zip(block["steps"], block["train_acc"], block["val_acc"]))
    return episodes(triples, bar, eval_every=1)


def qualify_episode(block: dict, ep: dict,
                    cfg: SpikeMicroscopyConfig) -> tuple[str, list[int]]:
    """('', baseline steps) when the episode enters the primary; otherwise a
    non-empty exclusion reason. Interior + >=min_baseline healthy pre-steps."""
    w0, w1 = block["w0"], block["w1"]
    if ep["censored"] or ep["start"] <= w0 or ep["end"] >= w1:
        return "edge_truncated", []
    lo = max(w0, ep["start"] - cfg.baseline_steps)
    idx0 = lo - w0
    base = [lo + i for i, v in
            enumerate(block["val_acc"][idx0: ep["start"] - w0])
            if v >= cfg.spike_bar]
    if len(base) < cfg.min_baseline:
        return "short_baseline", []
    return "", base


def _loss_break(block: dict, base_idx: list[int], start_idx: int,
                cfg: SpikeMicroscopyConfig) -> int | None:
    """First dense index before the val break where train_loss exceeds
    baseline median + k*MAD, sustained; None = no detectable precursor."""
    losses = block["train_loss"]
    base = [losses[i] for i in base_idx if losses[i] is not None]
    if not base:
        return None
    med = _median(base)
    mad = _median([abs(x - med) for x in base])
    thresh = med + cfg.loss_break_mads * mad if mad > 0 else 10 * med
    if thresh <= 0:
        return None
    scan0 = min(base_idx)
    for i in range(scan0, start_idx):
        run = losses[i: i + cfg.loss_break_sustain]
        if len(run) == cfg.loss_break_sustain \
                and all(x is not None and x > thresh for x in run):
            return i
    return None


def episode_metrics(cell: dict, block: dict, ep: dict, base: list[int],
                    cfg: SpikeMicroscopyConfig) -> dict:
    w0 = block["w0"]
    base_idx = [s - w0 for s in base]
    i0, i1 = ep["start"] - w0, ep["end"] - w0
    mean_power = torch.stack([block["power"][i] for i in base_idx]) \
        .mean(dim=0)
    ep_set = top_freqs([float(x) for x in mean_power], cfg.top_k)
    shares = _smooth([set_share(window_power(block, i), ep_set)
                      for i in range(len(block["steps"]))], cfg.smooth_window)
    baseline_share = _median([shares[i] for i in base_idx])
    ep_min_share = min(shares[i0: i1 + 1])
    r = ep_min_share / baseline_share if baseline_share > 0 else 0.0
    vals = block["val_acc"]
    argmin = min(range(i0, i1 + 1), key=lambda i: vals[i])
    min_val = vals[argmin]
    coarse_span = [v for s, _t, v in cell["coarse"]
                   if ep["start"] <= s <= ep["end"]]
    lb = _loss_break(block, base_idx, i0, cfg)
    post0, post1 = i1 + 1, min(len(vals), i1 + 1 + cfg.baseline_steps)
    post_idx = [i for i in range(post0, post1) if vals[i] >= cfg.spike_bar]
    rotated = None
    if len(post_idx) >= cfg.min_baseline:
        post_power = torch.stack([block["power"][i] for i in post_idx]) \
            .mean(dim=0)
        post_set = top_freqs([float(x) for x in post_power], cfg.top_k)
        rotated = sorted(post_set) != sorted(ep_set)
    base_grad = [block["grad_norm"][i] for i in base_idx
                 if block["grad_norm"][i] is not None]
    ep_grad = [g for g in block["grad_norm"][i0: i1 + 1] if g is not None]
    base_norm = _median([block["norm"][i] for i in base_idx])
    label = "preserved" if r >= cfg.preserve_bar else \
        "destroyed" if r <= cfg.destroy_bar else "mid"
    return {"lr": cell["lr"], "seed": cell["seed"], "w0": w0,
            "w1": block["w1"], "start": ep["start"], "end": ep["end"],
            "duration": ep["duration"], "min_val": round(min_val, 6),
            "argmin": block["steps"][argmin],
            "coarse_min": round(min(coarse_span), 6) if coarse_span else None,
            "baseline_share": round(baseline_share, 6),
            "min_share": round(ep_min_share, 6), "r": round(r, 6),
            "label": label, "ep_set": sorted(ep_set),
            "set_rotated": rotated,
            "lead": ep["start"] - (w0 + lb) if lb is not None else None,
            "grad_ratio": round(max(ep_grad) / _median(base_grad), 4)
            if ep_grad and base_grad and _median(base_grad) > 0 else None,
            "norm_base": round(base_norm, 4),
            "norm_min_ratio": round(min(block["norm"][i0: i1 + 1])
                                    / base_norm, 6),
            "fall": block["steps"][argmin] - ep["start"] + 1,
            "recovery": ep["end"] + 1 - block["steps"][argmin]}


def extract_episodes(cache: dict, cfg: SpikeMicroscopyConfig
                     ) -> tuple[list[dict], dict]:
    """All qualified episode rows across cells, plus the exclusion tally."""
    rows, excluded = [], {"edge_truncated": 0, "short_baseline": 0}
    for cell in cache["cells"]:
        for block in cell["dense"]:
            for ep in dense_episodes(block, cfg.spike_bar):
                reason, base = qualify_episode(block, ep, cfg)
                if reason:
                    excluded[reason] += 1
                    continue
                rows.append(episode_metrics(cell, block, ep, base, cfg))
    return rows, excluded


# ----------------------------------------------------------------- decide ----
def _g0(cache: dict, ref: dict, cfg: SpikeMicroscopyConfig) -> str:
    refs = {(c["lr"], c["seed"]): c for c in ref["cells"]}
    for cell in cache["cells"]:
        rc = refs.get((cell["lr"], cell["seed"]))
        if rc is None:
            return "reference_mismatch"
        by_step = {int(r[0]): r for r in rc["curve"]}
        coarse = {int(s): (t, v) for s, t, v in cell["coarse"]}
        for step in range(0, cell["rerun_end"] + 1, cfg.eval_every):
            row, ours = by_step.get(step), coarse.get(step)
            if row is None or ours is None or abs(row[1] - ours[0]) > 1e-9 \
                    or abs(row[2] - ours[1]) > 1e-9:
                return "reference_mismatch"
        for block in cell["dense"]:
            for i, step in enumerate(block["steps"]):
                vals = (block["train_acc"][i], block["val_acc"][i],
                        block["norm"][i])
                if not all(math.isfinite(v) for v in vals):
                    return "nonfinite"
                for key in ("train_loss", "grad_norm"):
                    x = block[key][i]
                    if x is None:
                        if step != cell["rerun_end"]:
                            return "nonfinite"
                    elif not math.isfinite(x):
                        return "nonfinite"
                if step % cfg.eval_every == 0:
                    t, v = coarse[step]
                    if abs(round(block["train_acc"][i], 6) - t) > 1e-9 \
                            or abs(round(block["val_acc"][i], 6) - v) > 1e-9:
                        return "dense_coarse_mismatch"
    return ""


def _g1(cache: dict, cfg: SpikeMicroscopyConfig) -> bool:
    if len(cache["cells"]) != len(cfg.cells):
        return False
    for cell, (lr, seed, rerun_end, windows) in zip(cache["cells"],
                                                    cfg.cells):
        if (cell["lr"], cell["seed"]) != (lr, seed) \
                or cell["rerun_end"] != rerun_end \
                or [tuple(w) for w in cell["windows"]] != list(windows):
            return False
        if len(cell["dense"]) != len(windows):
            return False
        for block, (w0, w1) in zip(cell["dense"], windows):
            if block["w0"] != w0 or block["w1"] != w1 \
                    or block["steps"] != list(range(w0, w1 + 1)):
                return False
    return True


def decide(cache: dict, ref: dict,
           cfg: SpikeMicroscopyConfig | None = None) -> dict:
    cfg = cfg or SpikeMicroscopyConfig()
    cfg.validate()
    info: dict = {"g1_complete": _g1(cache, cfg)}
    if not info["g1_complete"]:
        return info | {"verdict": "review", "reason": "grid_incomplete",
                       "g0_ok": False, "g2_bar_stable": False}
    g0_reason = _g0(cache, ref, cfg)
    info["g0_ok"] = g0_reason == ""
    if g0_reason:
        return info | {"verdict": "review", "reason": g0_reason,
                       "g2_bar_stable": False}
    rows, excluded = extract_episodes(cache, cfg)
    info |= {"episodes": rows, "excluded": excluded}

    def verdict_at(bar: float) -> str:
        deep = [e for e in rows if e["min_val"] < bar]
        if len(deep) < cfg.min_deep:
            return "review"
        n = {k: sum(1 for e in deep if e["label"] == k)
             for k in ("preserved", "destroyed", "mid")}
        if n["destroyed"] == 0 and n["preserved"] > n["mid"]:
            return "spike_preserves_circuit"
        if n["preserved"] == 0 and n["destroyed"] > n["mid"]:
            return "spike_destroys_circuit"
        if n["preserved"] >= 1 and n["destroyed"] >= 1:
            return "spike_mixed"
        return "review"

    deep = [e for e in rows if e["min_val"] < cfg.deep_bar]
    info |= {"n_episodes": len(rows), "n_deep": len(deep),
             "n_preserved": sum(1 for e in deep if e["label"] == "preserved"),
             "n_destroyed": sum(1 for e in deep if e["label"] == "destroyed"),
             "n_mid": sum(1 for e in deep if e["label"] == "mid"),
             "r_median_deep": round(_median([e["r"] for e in deep]), 6)
             if deep else None}
    leads = [e["lead"] for e in rows if e["lead"] is not None]
    grads = [e["grad_ratio"] for e in rows if e["grad_ratio"] is not None]
    hidden = [e["coarse_min"] - e["min_val"] for e in rows
              if e["coarse_min"] is not None]
    info |= {"lead_median": _median(leads) if leads else None,
             "n_lead_detected": len(leads),
             "grad_ratio_median": round(_median(grads), 4) if grads else None,
             "hidden_depth_median": round(_median(hidden), 6)
             if hidden else None,
             "n_fully_hidden": sum(1 for e in rows
                                   if e["coarse_min"] is None),
             "n_rotated": sum(1 for e in rows if e["set_rotated"]),
             "n_rotation_known": sum(1 for e in rows
                                     if e["set_rotated"] is not None)}
    by_bar = {bar: verdict_at(bar) for bar in cfg.deep_bars}
    info["verdict_by_bar"] = {str(b): v for b, v in by_bar.items()}
    info["g2_bar_stable"] = len(set(by_bar.values())) == 1
    if not info["g2_bar_stable"]:
        return info | {"verdict": "review", "reason": "bar_instability"}
    verdict = by_bar[cfg.deep_bar]
    reason = ""
    if verdict == "review":
        reason = "insufficient_deep" if len(deep) < cfg.min_deep \
            else "mid_band"
    return info | {"verdict": verdict, "reason": reason}


# ------------------------------------------------------------ report/figure ----
def build_report(cache: dict, ref: dict, info: dict,
                 cfg: SpikeMicroscopyConfig | None = None) -> dict:
    cfg = cfg or SpikeMicroscopyConfig()
    summary = {
        "verdict": info["verdict"], "reason": info["reason"],
        "status": "pass" if info["verdict"] != "review" else "review",
        "scope": "own_committed_trajectories_dense_reobservation_"
                 "embedding_fourier_only",
        "g0_ok": info.get("g0_ok"), "g1_complete": info["g1_complete"],
        "g2_bar_stable": info.get("g2_bar_stable"),
        "n_episodes": info.get("n_episodes"), "n_deep": info.get("n_deep"),
        "n_preserved": info.get("n_preserved"),
        "n_destroyed": info.get("n_destroyed"), "n_mid": info.get("n_mid"),
        "r_median_deep": info.get("r_median_deep"),
        "excluded": info.get("excluded"),
        "lead_median": info.get("lead_median"),
        "n_lead_detected": info.get("n_lead_detected"),
        "grad_ratio_median": info.get("grad_ratio_median"),
        "hidden_depth_median": info.get("hidden_depth_median"),
        "n_fully_hidden": info.get("n_fully_hidden"),
        "n_rotated": info.get("n_rotated"),
        "n_rotation_known": info.get("n_rotation_known"),
        "verdict_by_bar": info.get("verdict_by_bar"),
        "runs": cache.get("runs"), "total_steps": cache.get("total_steps"),
    }
    return {"schema": SCHEMA, "generated_at": cache["generated_at"],
            "summary": summary, "episodes": info.get("episodes", [])}


def summarize(report: dict) -> list[str]:
    s = report["summary"]
    lines = [f"decision={s['verdict']} reason={s['reason']}"
             f" scope={s['scope']}",
             f"g0={s['g0_ok']} g1={s['g1_complete']} g2={s['g2_bar_stable']}"
             f" runs={s['runs']} total_steps={s['total_steps']}",
             f"episodes={s['n_episodes']} deep={s['n_deep']}"
             f" preserved={s['n_preserved']} destroyed={s['n_destroyed']}"
             f" mid={s['n_mid']} r_median_deep={s['r_median_deep']}"
             f" excluded={s['excluded']}",
             f"lead_median={s['lead_median']}"
             f" (n={s['n_lead_detected']})"
             f" grad_ratio_median={s['grad_ratio_median']}"
             f" hidden_depth_median={s['hidden_depth_median']}"
             f" fully_hidden={s['n_fully_hidden']}"
             f" rotated={s['n_rotated']}/{s['n_rotation_known']}"]
    for e in report["episodes"]:
        lines.append(
            f"lr={e['lr']} seed={e['seed']} ep[{e['start']},{e['end']}]:"
            f" min_val={e['min_val']} (coarse {e['coarse_min']})"
            f" r={e['r']} {e['label']}"
            f" lead={e['lead']} grad_ratio={e['grad_ratio']}"
            f" fall={e['fall']} recovery={e['recovery']}"
            f" rotated={e['set_rotated']}")
    return lines


def plot_result(cache: dict, info: dict, path) -> None:
    """One file, two panels: (a) the deepest qualified episode at step
    resolution -- val/train acc, share ratio, norm ratio, with the 100-step
    grid overlaid as dots (what v1287/v1288 could see); (b) r vs dense
    min val for every qualified episode -- the verdict panel."""
    plt = agg_pyplot()

    cfg = SpikeMicroscopyConfig()  # display constants are preregistered
    rows = info.get("episodes", [])
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.5, 4.6),
                                 gridspec_kw={"width_ratios": [3, 2]})
    if rows:
        star = min(rows, key=lambda e: e["min_val"])
        cell = next(c for c in cache["cells"]
                    if (c["lr"], c["seed"]) == (star["lr"], star["seed"]))
        block = next(b for b in cell["dense"] if b["w0"] == star["w0"])
        lo = max(block["w0"], star["start"] - 250)
        hi = min(block["w1"], star["end"] + 250)
        sel = [i for i, s in enumerate(block["steps"]) if lo <= s <= hi]
        xs = [block["steps"][i] for i in sel]
        ep_set = star["ep_set"]
        shares = _smooth([set_share(window_power(block, i), ep_set)
                          for i in range(len(block["steps"]))],
                         cfg.smooth_window)
        base = star["baseline_share"]
        ax.plot(xs, [block["val_acc"][i] for i in sel], "-",
                color="tab:blue", linewidth=1.2, label="val acc (dense)")
        ax.plot(xs, [block["train_acc"][i] for i in sel], "-",
                color="tab:orange", linewidth=0.9, alpha=0.8,
                label="train acc (dense)")
        ax.plot(xs, [shares[i] / base for i in sel], "-",
                color="tab:green", linewidth=1.4,
                label="top-5 share / baseline")
        nb = star["norm_base"]
        ax.plot(xs, [block["norm"][i] / nb for i in sel], "--",
                color="gray", linewidth=1.0, label="total norm / baseline")
        cg = [(s, v) for s, _t, v in cell["coarse"] if lo <= s <= hi]
        ax.plot([s for s, _ in cg], [v for _, v in cg], "o",
                color="black", markersize=4, label="100-step grid (val)")
        ax.set(xlabel="step", ylabel="value",
               title=f"deepest episode: lr={star['lr']} seed={star['seed']}"
                     f" min_val={star['min_val']} r={star['r']}")
        ax.set_ylim(0, 1.35)
        ax.legend(fontsize=6.5, loc="lower left")
    colors = {1e-3: "black", 2e-3: "tab:green", 4e-3: "tab:blue",
              8e-3: "tab:purple"}
    seen = set()
    for e in rows:
        label = f"lr={e['lr']}" if e["lr"] not in seen else None
        seen.add(e["lr"])
        bx.plot(e["min_val"], e["r"], "o", color=colors.get(e["lr"], "red"),
                markersize=6, label=label)
    bx.axhline(cfg.preserve_bar, color="tab:green", linestyle=":",
               alpha=0.8)
    bx.axhline(cfg.destroy_bar, color="tab:red", linestyle=":", alpha=0.8)
    bx.axvline(cfg.deep_bar, color="gray", linestyle=":", alpha=0.8)
    bx.set(xlabel="dense min val (episode)", ylabel="r = min/base share",
           xlim=(-0.02, 1.0), ylim=(0, 1.3),
           title=f"circuit persistence: {info['verdict']}")
    bx.legend(fontsize=7)
    fig.tight_layout()
    save_figure(fig, path)
