"""v1279: why do narrow models grok faster? The norm-clock causal test.

Re-measures the width -> t_gen curve in one harness (phenomenon arm), then
intervenes on init scale at fixed width d=128 (alpha arm + a matched-norm arm
whose init total norm equals a d=32 model's). The preregistered ladder decides
between norm-clock mediation, partial mediation, rejection, and the honest
possibility that v1277's cross-harness observation was not robust.

Preregistered before any GPU run (see docs/v1279-grok-speed-brief.md).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import torch

from minigpt.grok_checkpoint_v1185 import train_to_grok
from minigpt.grok_predict_v1186 import evaluate_table
from minigpt.grok_v1179 import GrokConfig, make_grok_model, seed_everything
from minigpt.report_utils import utc_now

VERDICTS = (
    "narrow_speedup_is_norm_clock",
    "norm_clock_partial",
    "norm_clock_rejected",
    "phenomenon_not_robust",
    "review",
)


@dataclass(frozen=True)
class SpeedConfig:
    p: int = 97
    train_frac: float = 0.2
    weight_decay: float = 1.0
    n_head: int = 4
    max_steps: int = 40000
    widths: tuple[int, ...] = (16, 32, 64, 128)
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    wide: int = 128
    narrow: int = 32
    alphas_wide: tuple[float, ...] = (0.5, 2.0)
    alpha_narrow: float = 2.0
    grok_bar: float = 0.90
    tgen_bars: tuple[float, ...] = (0.85, 0.90, 0.95)
    ratio_bar: float = 2.0
    share_full: float = 0.5
    share_partial: float = 0.2
    sign_pass: int = 5
    sign_fail: int = 3
    max_runs: int = 28

    def validate(self) -> None:
        if any(w % self.n_head != 0 for w in self.widths):
            raise ValueError("every width must be divisible by n_head")
        if self.wide not in self.widths or self.narrow not in self.widths:
            raise ValueError("wide and narrow must be grid widths")
        expected = self.cell_count()
        if expected + 1 > self.max_runs:
            raise ValueError("planned cells plus probe exceed the GPU budget")
        if not set(self.tgen_bars) >= {self.grok_bar}:
            raise ValueError("grok_bar must be on the robustness grid")

    def cell_count(self) -> int:
        return (len(self.widths) * len(self.seeds)
                + len(self.alphas_wide) * len(self.seeds)
                + len(self.seeds)      # matched-norm arm
                + len(self.seeds))     # symmetry arm


# ---------------------------------------------------------------- helpers ----
def scaled_init(width: int, seed: int, alpha: float, cfg: SpeedConfig) -> dict:
    """The seeded standard init state with every tensor multiplied by alpha."""
    seed_everything(seed)
    model = make_grok_model(cfg.p + 2, GrokConfig(n_embd=width, n_head=cfg.n_head,
                                                  seeds=(seed,), wds=(cfg.weight_decay,)))
    return {k: v.detach().clone() * alpha for k, v in model.state_dict().items()}


def total_norm_of(state: dict) -> float:
    return float(torch.sqrt(sum((v.float() ** 2).sum() for v in state.values())))


def t_gen_at(curve: list[tuple[int, float]], bar: float) -> int | None:
    """First eval step whose val accuracy reaches bar; None = censored."""
    for step, val_acc in curve:
        if val_acc >= bar:
            return step
    return None


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return math.nan
    mid = n // 2
    return float(ordered[mid]) if n % 2 else float((ordered[mid - 1] + ordered[mid]) / 2)


def _cell_tgen(cell: dict, bar: float) -> float:
    t = t_gen_at([tuple(x) for x in cell["curve"]], bar)
    return math.inf if t is None else float(t)


# ---------------------------------------------------------------- phase A ----
def train_cell(cfg: SpeedConfig, width: int, seed: int, alpha: float, device) -> dict:
    init = scaled_init(width, seed, alpha, cfg)
    n0 = total_norm_of(init)
    grok_cfg = GrokConfig(p=cfg.p, train_frac=cfg.train_frac, n_head=cfg.n_head,
                          n_embd=width, max_steps=cfg.max_steps,
                          seeds=(seed,), wds=(cfg.weight_decay,))
    model, meta, curve = train_to_grok(grok_cfg, device, init_state=init)
    heldout = evaluate_table(model, meta)["heldout_acc"]
    n_final = total_norm_of(model.state_dict())
    val_curve = [(int(row["step"]), float(row["val_acc"])) for row in curve]
    return {
        "width": width, "seed": seed, "alpha": alpha,
        "n0": round(n0, 4), "n_final": round(n_final, 4),
        "t_mem": meta.t_mem, "t_gen": meta.t_gen, "steps_run": meta.steps_run,
        "final_train_acc": round(meta.final_train_acc, 6),
        "final_val_acc": round(meta.final_val_acc, 6),
        "heldout_acc": round(heldout, 6),
        "curve": val_curve,
    }


def run_phase_a(cfg: SpeedConfig, device, trainer=train_cell) -> dict:
    cfg.validate()
    cells = []
    for width in cfg.widths:
        for seed in cfg.seeds:
            cells.append(trainer(cfg, width, seed, 1.0, device) | {"arm": "grid"})
    for alpha in cfg.alphas_wide:
        for seed in cfg.seeds:
            cells.append(trainer(cfg, cfg.wide, seed, alpha, device) | {"arm": "alpha_wide"})
    for seed in cfg.seeds:
        narrow_n0 = total_norm_of(scaled_init(cfg.narrow, seed, 1.0, cfg))
        wide_n0 = total_norm_of(scaled_init(cfg.wide, seed, 1.0, cfg))
        alpha_star = narrow_n0 / wide_n0
        cells.append(trainer(cfg, cfg.wide, seed, alpha_star, device) | {"arm": "alpha_star"})
    for seed in cfg.seeds:
        cells.append(trainer(cfg, cfg.narrow, seed, cfg.alpha_narrow, device)
                     | {"arm": "alpha_narrow"})
    return {"schema": "grok_speed_v1279.v1", "generated_at": utc_now(),
            "config": {"widths": list(cfg.widths), "seeds": list(cfg.seeds),
                       "alphas_wide": list(cfg.alphas_wide), "wide": cfg.wide,
                       "narrow": cfg.narrow, "max_steps": cfg.max_steps},
            "cells": cells}


# ---------------------------------------------------------------- phase B ----
def _grid_medians(cells: list[dict], cfg: SpeedConfig, bar: float) -> dict[int, float]:
    medians = {}
    for width in cfg.widths:
        grokked = [c for c in cells
                   if c["arm"] == "grid" and c["width"] == width
                   and c["heldout_acc"] >= cfg.grok_bar
                   and _cell_tgen(c, bar) != math.inf]
        medians[width] = _median([_cell_tgen(c, bar) for c in grokked])
    return medians


def _phenomenon(medians: dict[int, float], cfg: SpeedConfig) -> str:
    ordered = [medians[w] for w in sorted(cfg.widths)]
    if any(math.isnan(m) for m in ordered):
        return "review"
    ratio = medians[max(cfg.widths)] / medians[min(cfg.widths)]
    non_increasing = all(ordered[i] <= ordered[i + 1] for i in range(len(ordered) - 1))
    if ratio >= cfg.ratio_bar and non_increasing:
        return "confirmed"
    if ratio >= cfg.ratio_bar:
        return "review"
    return "not_robust"


def _alpha_sign(cells: list[dict], cfg: SpeedConfig, bar: float) -> dict:
    count, total = 0, 0
    for seed in cfg.seeds:
        by_alpha = {}
        for c in cells:
            if c["width"] == cfg.wide and c["seed"] == seed and c["arm"] in ("grid", "alpha_wide"):
                by_alpha[c["alpha"]] = _cell_tgen(c, bar)
        ladder = sorted(by_alpha)
        for low, high in zip(ladder, ladder[1:]):
            total += 1
            if by_alpha[low] < by_alpha[high]:
                count += 1
    if count >= cfg.sign_pass:
        state = "pass"
    elif count <= cfg.sign_fail:
        state = "fail"
    else:
        state = "review"
    return {"monotone_pairs": count, "total_pairs": total, "state": state}


def _mediation(cells: list[dict], cfg: SpeedConfig, bar: float) -> dict:
    wide_base = _median([_cell_tgen(c, bar) for c in cells
                         if c["arm"] == "grid" and c["width"] == cfg.wide])
    narrow_base = _median([_cell_tgen(c, bar) for c in cells
                           if c["arm"] == "grid" and c["width"] == cfg.narrow])
    matched = _median([_cell_tgen(c, bar) for c in cells if c["arm"] == "alpha_star"])
    gap = wide_base - narrow_base
    share = math.nan
    if gap > 0 and not math.isinf(matched):
        share = 1.0 - (matched - narrow_base) / gap
    elif math.isinf(matched):
        share = -math.inf
    return {"wide_base": wide_base, "narrow_base": narrow_base,
            "matched": matched, "gap": gap, "share": share}


def _verdict_at_bar(cells: list[dict], cfg: SpeedConfig, bar: float) -> dict:
    medians = _grid_medians(cells, cfg, bar)
    phen = _phenomenon(medians, cfg)
    sign = _alpha_sign(cells, cfg, bar)
    med = _mediation(cells, cfg, bar)
    if phen == "not_robust":
        verdict = "phenomenon_not_robust"
    elif phen == "review" or sign["state"] == "review":
        verdict = "review"
    elif sign["state"] == "fail":
        verdict = "norm_clock_rejected"
    elif med["share"] >= cfg.share_full:
        verdict = "narrow_speedup_is_norm_clock"
    elif med["share"] >= cfg.share_partial:
        verdict = "norm_clock_partial"
    else:
        verdict = "norm_clock_rejected"
    return {"bar": bar, "verdict": verdict, "phenomenon": phen,
            "medians": {str(w): medians[w] for w in sorted(medians)},
            "sign": sign, "mediation": med}


def decide(cache: dict, cfg: SpeedConfig | None = None) -> dict:
    cfg = cfg or SpeedConfig()
    cells = cache["cells"]
    g0 = all(
        sum(1 for c in cells
            if c["arm"] == "grid" and c["width"] == width
            and c["heldout_acc"] >= cfg.grok_bar and c["t_gen"] is not None) >= 2
        for width in cfg.widths
    )
    g1 = len(cells) == cfg.cell_count()
    ladder = [_verdict_at_bar(cells, cfg, bar) for bar in cfg.tgen_bars]
    main = next(entry for entry in ladder if entry["bar"] == cfg.grok_bar)
    g2 = len({entry["verdict"] for entry in ladder}) == 1
    if not g0:
        verdict, reason = "review", "substrate_unsound"
    elif not g1:
        verdict, reason = "review", "grid_incomplete"
    elif not g2:
        verdict, reason = "review", "bar_unstable"
    else:
        verdict, reason = main["verdict"], main["verdict"]
    symmetry = [_cell_tgen(c, cfg.grok_bar) for c in cells if c["arm"] == "alpha_narrow"]
    return {
        "status": "pass",
        "verdict": verdict,
        "reason": reason,
        "g0_substrate": g0,
        "g1_complete": g1,
        "g2_bar_stable": g2,
        "main": main,
        "ladder": ladder,
        "symmetry_tgen_narrow_alpha2": symmetry,
        "scope": "own_grokked_substrate_toy_scale_frozen_recipe",
    }


# ----------------------------------------------------------------- report ----
def build_report(cache: dict, info: dict, generated_at: str | None = None) -> dict:
    cfg = SpeedConfig()
    rows = []
    for c in cache["cells"]:
        t = _cell_tgen(c, cfg.grok_bar)
        rows.append({
            "arm": c["arm"], "width": c["width"], "seed": c["seed"],
            "alpha": round(c["alpha"], 4), "n0": c["n0"], "n_final": c["n_final"],
            "heldout_acc": c["heldout_acc"],
            "t_gen": None if math.isinf(t) else int(t),
            "censored": math.isinf(t),
        })
    main = info["main"]
    flat = {
        "verdict": info["verdict"],
        "reason": info["reason"],
        "scope": info["scope"],
        "g0_substrate": info["g0_substrate"],
        "g1_complete": info["g1_complete"],
        "g2_bar_stable": info["g2_bar_stable"],
        "phenomenon": main["phenomenon"],
        "ratio_wide_over_narrowest": (
            round(main["medians"][str(max(cfg.widths))]
                  / main["medians"][str(min(cfg.widths))], 3)
            if main["medians"][str(min(cfg.widths))] else None),
        "alpha_monotone_pairs": f"{main['sign']['monotone_pairs']}/{main['sign']['total_pairs']}",
        "mediation_share": (None if math.isnan(main["mediation"]["share"])
                            else round(main["mediation"]["share"], 4)),
        "matched_alpha_tgen": main["mediation"]["matched"],
        "wide_base_tgen": main["mediation"]["wide_base"],
        "narrow_base_tgen": main["mediation"]["narrow_base"],
    }
    return {
        "schema_version": 1,
        "title": "MiniGPT v1279 narrow-grok-speed norm-clock test",
        "description": "Preregistered width/init-scale intervention on time-to-grok.",
        "generated_at": generated_at or utc_now(),
        "status": info["status"],
        "decision": info["verdict"],
        "summary": flat,
        "ladder": info["ladder"],
        "cells": rows,
        "artifacts": [],
        "recommendations": _recommendations(info),
        "warnings": [],
    }


def _recommendations(info: dict) -> list[str]:
    v = info["verdict"]
    if v == "narrow_speedup_is_norm_clock":
        return ["Model width choices trade capacity against the wd norm-clock; test "
                "whether lr*wd rescaling collapses the t_gen curves onto one clock."]
    if v == "norm_clock_partial":
        return ["Quantify the residual width effect at matched norm; candidate "
                "follow-ups: memorization-basin depth or circuit search-space size."]
    if v == "norm_clock_rejected":
        return ["The speedup is not an init-norm effect; probe optimizer dynamics "
                "(per-parameter Adam scale) or data-fit capacity next."]
    if v == "phenomenon_not_robust":
        return ["v1277's cross-harness comparison overstated the effect; record the "
                "corrected same-harness curve as the reference."]
    return ["Adjudicate the review branch externally before any follow-up."]


def summarize(report: dict) -> list[str]:
    lines = [f"status={report['status']}", f"decision={report['decision']}"]
    lines += [f"{key}={value}" for key, value in report["summary"].items()]
    for entry in report["ladder"]:
        lines.append(
            f"bar={entry['bar']}: verdict={entry['verdict']} phen={entry['phenomenon']} "
            f"sign={entry['sign']['monotone_pairs']}/{entry['sign']['total_pairs']} "
            f"share={entry['mediation']['share']}"
        )
    for row in report["cells"]:
        lines.append(
            f"{row['arm']} w={row['width']} seed={row['seed']} a={row['alpha']}: "
            f"acc={row['heldout_acc']} t_gen={row['t_gen']} n0={row['n0']}"
        )
    return lines


def plot_result(cache: dict, info: dict, path) -> None:
    """One figure: t_gen vs width (grid) with the d=128 alpha arms overlaid."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pathlib import Path as _Path

    cfg = SpeedConfig()
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for c in cache["cells"]:
        t = _cell_tgen(c, cfg.grok_bar)
        y = cfg.max_steps * 1.15 if math.isinf(t) else t
        marker = {"grid": "o", "alpha_wide": "^", "alpha_star": "*",
                  "alpha_narrow": "s"}[c["arm"]]
        color = {"grid": "tab:blue", "alpha_wide": "tab:orange",
                 "alpha_star": "tab:red", "alpha_narrow": "tab:green"}[c["arm"]]
        ax.scatter(c["width"], y, marker=marker, color=color, zorder=3,
                   s=90 if c["arm"] == "alpha_star" else 40)
    ax.axhline(cfg.max_steps, color="gray", linestyle=":", label="step budget (censored above)")
    ax.set(xscale="log", yscale="log", xlabel="n_embd (width, log)",
           ylabel="t_gen (steps, log)",
           title=f"v1279 norm-clock: {info['verdict']}")
    ax.set_xticks(list(cfg.widths), [str(w) for w in cfg.widths])
    handles = [plt.Line2D([], [], marker=m, color=col, linestyle="",
                          label=lab) for m, col, lab in
               [("o", "tab:blue", "grid α=1"), ("^", "tab:orange", "d=128 α∈{0.5,2}"),
                ("*", "tab:red", "d=128 matched-norm α*"), ("s", "tab:green", "d=32 α=2")]]
    ax.legend(handles=handles, fontsize=8)
    fig.tight_layout()
    out = _Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)
