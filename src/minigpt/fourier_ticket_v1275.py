"""v1275: test whether the grokking lottery ticket preserves its Fourier circuit.

Arm P prunes the frozen v1185 checkpoint on CPU. Arm L rewinds a magnitude
ticket and matched controls to initialization, trains once on GPU, and caches
all measurements. Analysis and ``decide`` are pure functions over that cache.
Scope: toy modular addition on this repository's own substrate.
"""

from __future__ import annotations

import copy
import hashlib
import math
from dataclasses import dataclass, replace
from pathlib import Path

import torch

from minigpt.experiment_utils import mean_std
from minigpt.grok_checkpoint_v1185 import CANONICAL_CONFIG, CheckpointMeta, load_checkpoint, train_to_grok
from minigpt.grok_interp_v1188 import concentration_metrics, embedding_spectrum, number_embedding
from minigpt.grok_predict_v1186 import evaluate_table
from minigpt.grok_v1179 import GrokConfig, make_grok_model
from minigpt.report_utils import utc_now
from minigpt.script_runtime import seed_everything

KNOWN_FREQS = (43, 3, 48, 26, 44)
CKPT_SHA256 = "46F2A11A945F0BD140AF09FE298B28DD31062B4E3018EA159876C263F7DCB7DB"


@dataclass(frozen=True)
class TicketConfig:
    sparsities: tuple[float, ...] = (0.50, 0.70, 0.80, 0.90, 0.95)
    modes: tuple[str, ...] = ("per_tensor", "global")
    random_seeds: tuple[int, ...] = (71, 72, 73, 74, 75)
    train_seeds: tuple[int, ...] = (1337, 1338, 1339)
    requested_levels: tuple[float, ...] = (0.50, 0.75, 0.875)
    run_levels: tuple[float, ...] = (0.50,)
    acc_floor: float = 0.90
    align_margin: float = 0.05
    share_tolerance: float = 0.05
    overlap_min: int = 4
    max_runs_per_seed: int = 5
    expected_sha256: str = CKPT_SHA256
    known_freqs: tuple[int, ...] = KNOWN_FREQS


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def prune_targets(model) -> dict[str, torch.nn.Parameter]:
    """Unique tied embedding/unembed parameter plus MLP matrices."""
    return {
        name: param
        for name, param in model.named_parameters()
        if name == "token_embedding.weight" or (".mlp." in name and name.endswith(".weight"))
    }


def _select_mask(scores: torch.Tensor, keep: int, gen: torch.Generator | None) -> torch.Tensor:
    flat = scores.detach().abs().cpu().reshape(-1)
    keep = max(1, min(int(keep), flat.numel()))
    chosen = torch.randperm(flat.numel(), generator=gen)[:keep] if gen else torch.topk(flat, keep).indices
    mask = torch.zeros(flat.numel(), dtype=torch.bool)
    mask[chosen] = True
    return mask.reshape(scores.shape)


def make_mask(
    model,
    sparsity: float,
    mode: str,
    *,
    random_seed: int | None = None,
) -> dict[str, torch.Tensor]:
    if not 0.0 <= sparsity < 1.0:
        raise ValueError("sparsity must be in [0, 1)")
    if mode not in {"per_tensor", "global"}:
        raise ValueError("mode must be per_tensor or global")
    targets = prune_targets(model)
    gen = torch.Generator().manual_seed(random_seed) if random_seed is not None else None
    if mode == "per_tensor":
        return {
            name: _select_mask(param, round(param.numel() * (1.0 - sparsity)), gen)
            for name, param in targets.items()
        }

    names = list(targets)
    sizes = [targets[name].numel() for name in names]
    flat = torch.cat([targets[name].detach().abs().cpu().reshape(-1) for name in names])
    joined = _select_mask(flat, round(flat.numel() * (1.0 - sparsity)), gen).reshape(-1)
    masks: dict[str, torch.Tensor] = {}
    offset = 0
    for name, size in zip(names, sizes):
        masks[name] = joined[offset : offset + size].reshape(targets[name].shape)
        offset += size
    return masks


def mask_sparsity(masks: dict[str, torch.Tensor]) -> float:
    total = sum(mask.numel() for mask in masks.values())
    kept = sum(int(mask.sum()) for mask in masks.values())
    return round(1.0 - kept / total, 6)


def masked_copy(model, masks: dict[str, torch.Tensor]):
    clone = copy.deepcopy(model)
    with torch.no_grad():
        for name, param in prune_targets(clone).items():
            param.mul_(masks[name].to(device=param.device, dtype=param.dtype))
    return clone


def freq_stats(model, p: int, known_freqs: tuple[int, ...] = KNOWN_FREQS) -> dict:
    power = embedding_spectrum(number_embedding(model, p))
    metrics = concentration_metrics(power, top_k=len(known_freqs))
    valid = [freq for freq in known_freqs if 1 <= freq <= power.numel()]
    top_freqs = metrics["top_freqs"]
    return {
        "known_share": round(sum(float(power[freq - 1]) for freq in valid), 6),
        "top5_share": metrics["top_k_fraction"],
        "top_freqs": top_freqs,
        "known_overlap": len(set(top_freqs) & set(valid)),
    }


def _measure(model, meta: CheckpointMeta, masks, known_freqs) -> dict:
    candidate = masked_copy(model, masks)
    table = evaluate_table(candidate, meta)
    return {"heldout_acc": table["heldout_acc"], **freq_stats(candidate, meta.p, known_freqs)}


def run_arm_p(model, meta: CheckpointMeta, cfg: TicketConfig) -> dict:
    full = {"heldout_acc": evaluate_table(model, meta)["heldout_acc"], **freq_stats(model, meta.p, cfg.known_freqs)}
    rows = []
    for mode in cfg.modes:
        for sparsity in cfg.sparsities:
            masks = make_mask(model, sparsity, mode)
            measured = _measure(model, meta, masks, cfg.known_freqs)
            controls = [
                _measure(model, meta, make_mask(model, sparsity, mode, random_seed=seed), cfg.known_freqs)
                for seed in cfg.random_seeds
            ]
            rand_acc = mean_std([row["heldout_acc"] for row in controls])
            rand_share = mean_std([row["known_share"] for row in controls])
            rows.append(
                {
                    "mode": mode,
                    "sparsity": sparsity,
                    "actual_sparsity": mask_sparsity(masks),
                    **measured,
                    "random_acc_mean": round(rand_acc[0], 6),
                    "random_acc_std": round(rand_acc[1], 6),
                    "random_share_mean": round(rand_share[0], 6),
                    "random_share_std": round(rand_share[1], 6),
                    "share_margin": round(measured["known_share"] - rand_share[0], 6),
                    "random_trials": len(controls),
                }
            )
    return {"full": full, "rows": rows}


def arm_p_result(arm_p: dict, cfg: TicketConfig) -> dict:
    rows = arm_p.get("rows", [])
    probe = all(
        any(row["mode"] == mode and row["sparsity"] == 0.5 and row["heldout_acc"] >= cfg.acc_floor for row in rows)
        for mode in cfg.modes
    )
    selected = {}
    for mode in cfg.modes:
        eligible = [row for row in rows if row["mode"] == mode and row["heldout_acc"] >= cfg.acc_floor]
        selected[mode] = max(eligible, key=lambda row: row["sparsity"]) if eligible else None
    aligned = all(selected[mode] is not None and selected[mode]["share_margin"] >= cfg.align_margin for mode in cfg.modes)
    return {"probe_ok": probe, "p_pass": probe and aligned, "selected": selected}


def _grok_cfg(seed: int, max_steps: int = 40000) -> GrokConfig:
    return replace(CANONICAL_CONFIG, seeds=(seed,), wds=(1.0,), max_steps=max_steps)


def _initial_state(cfg: GrokConfig, init_seed: int) -> dict[str, torch.Tensor]:
    seed_everything(init_seed)
    model = make_grok_model(cfg.p + 2, cfg)
    return {name: value.detach().clone() for name, value in model.state_dict().items()}


def _run_record(arm: str, level: float, model, meta: CheckpointMeta, step_cap: int, dense_stats: dict | None, cfg) -> dict:
    stats = freq_stats(model, meta.p, cfg.known_freqs)
    overlap = stats["known_overlap"]
    share_gap = stats["known_share"] - dense_stats["known_share"] if dense_stats else 0.0
    return {
        "seed": meta.seed,
        "arm": arm,
        "sparsity": level,
        "t_gen": meta.t_gen,
        "steps_run": meta.steps_run,
        "step_cap": step_cap,
        "heldout_acc": meta.final_val_acc,
        "grokked": meta.t_gen is not None and meta.t_gen <= step_cap and meta.final_val_acc >= cfg.acc_floor,
        **stats,
        "share_gap": round(share_gap, 6),
        "circuit_aligned": bool(dense_stats is None or (share_gap >= -cfg.share_tolerance and overlap >= cfg.overlap_min)),
    }


def run_arm_l(cfg: TicketConfig, device: torch.device) -> dict:
    rows = []
    for seed in cfg.train_seeds:
        dense_cfg = _grok_cfg(seed)
        init_state = _initial_state(dense_cfg, seed)
        dense, dense_meta, _ = train_to_grok(dense_cfg, device, init_state=init_state)
        dense_stats = freq_stats(dense, dense_meta.p, cfg.known_freqs)
        rows.append(_run_record("dense", 0.0, dense, dense_meta, dense_cfg.max_steps, None, cfg))
        if dense_meta.t_gen is None:
            continue
        step_cap = int(math.ceil(1.5 * dense_meta.t_gen / dense_cfg.eval_every) * dense_cfg.eval_every)
        sparse_cfg = _grok_cfg(seed, step_cap)
        for level in cfg.run_levels:
            ticket_mask = make_mask(dense, level, "global")
            random_mask = make_mask(dense, level, "global", random_seed=5000 + seed)
            arms = (
                ("ticket", ticket_mask, init_state),
                ("random", random_mask, init_state),
                ("reinit", ticket_mask, _initial_state(dense_cfg, 10000 + seed)),
            )
            for arm, masks, state in arms:
                model, meta, _ = train_to_grok(sparse_cfg, device, init_state=state, masks=masks)
                rows.append(_run_record(arm, level, model, meta, step_cap, dense_stats, cfg))
    return {
        "rows": rows,
        "requested_levels": list(cfg.requested_levels),
        "run_levels": list(cfg.run_levels),
        "descoped_levels": [level for level in cfg.requested_levels if level not in cfg.run_levels],
        "max_runs": len(cfg.train_seeds) * cfg.max_runs_per_seed,
        "actual_runs": len(rows),
    }


def run_phase_a(checkpoint: str | Path, cfg: TicketConfig, device: torch.device) -> dict:
    before = file_sha256(checkpoint)
    if before != cfg.expected_sha256:
        raise ValueError(f"checkpoint hash mismatch: {before}")
    model, meta = load_checkpoint(checkpoint, device=torch.device("cpu"))
    arm_p = run_arm_p(model, meta, cfg)
    p_info = arm_p_result(arm_p, cfg)
    arm_l = run_arm_l(cfg, device) if p_info["probe_ok"] else {
        "rows": [], "skipped_reason": "arm_p_probe_failed", "actual_runs": 0,
        "max_runs": len(cfg.train_seeds) * cfg.max_runs_per_seed,
        "requested_levels": list(cfg.requested_levels), "run_levels": [],
        "descoped_levels": list(cfg.requested_levels),
    }
    return {
        "schema_version": 1,
        "config": {
            "sparsities": list(cfg.sparsities), "modes": list(cfg.modes),
            "random_seeds": list(cfg.random_seeds), "train_seeds": list(cfg.train_seeds),
            "acc_floor": cfg.acc_floor, "align_margin": cfg.align_margin,
            "share_tolerance": cfg.share_tolerance, "overlap_min": cfg.overlap_min,
            "known_freqs": list(cfg.known_freqs), "expected_sha256": cfg.expected_sha256,
        },
        "checkpoint": str(checkpoint), "checkpoint_sha_before": before,
        "arm_p": arm_p, "arm_l": arm_l, "checkpoint_sha_after": file_sha256(checkpoint),
    }


def decide(cache: dict, cfg: TicketConfig) -> dict:
    arm_p = cache.get("arm_p", {})
    p_info = arm_p_result(arm_p, cfg)
    p_rows = arm_p.get("rows", [])
    p_complete = len(p_rows) == len(cfg.sparsities) * len(cfg.modes)
    random_complete = all(row.get("random_trials") == len(cfg.random_seeds) for row in p_rows)
    l_rows = cache.get("arm_l", {}).get("rows", [])
    expected_l = len(cfg.train_seeds) * (1 + 3 * len(cfg.run_levels))
    l_complete = len(l_rows) == expected_l
    budget_ok = cache.get("arm_l", {}).get("actual_runs", 0) <= len(cfg.train_seeds) * cfg.max_runs_per_seed
    hash_ok = cache.get("checkpoint_sha_before") == cfg.expected_sha256 == cache.get("checkpoint_sha_after")
    valid_l = (not p_info["probe_ok"] and cache.get("arm_l", {}).get("skipped_reason") == "arm_p_probe_failed") or l_complete
    status = "pass" if hash_ok and p_complete and random_complete and valid_l and budget_ok else "review"

    ticket = [row for row in l_rows if row["arm"] == "ticket"]
    random_rows = [row for row in l_rows if row["arm"] == "random"]
    reinit = [row for row in l_rows if row["arm"] == "reinit"]
    ticket_groks = len(ticket) == len(cfg.train_seeds) and all(row["grokked"] for row in ticket)
    ticket_count = sum(row["grokked"] for row in ticket)
    control_count = max(sum(row["grokked"] for row in random_rows), sum(row["grokked"] for row in reinit))
    control_tie = bool(ticket and control_count >= ticket_count)
    tickets_aligned = bool(ticket) and all(row["circuit_aligned"] for row in ticket)
    if not p_info["p_pass"]:
        verdict = "pruning_breaks_circuit"
    elif not ticket_groks or control_tie:
        verdict = "ticket_needs_dense_start"
    elif tickets_aligned:
        verdict = "ticket_matches_fourier_circuit"
    else:
        verdict = "ticket_trains_but_unaligned"
    return {
        "status": status, "verdict": verdict,
        "gates": {
            "checkpoint_unchanged": hash_ok, "p_complete": p_complete,
            "random_controls_complete": random_complete, "arm_p_probe_ok": p_info["probe_ok"],
            "arm_p_aligned": p_info["p_pass"], "arm_l_complete": l_complete,
            "arm_l_skipped": not p_info["probe_ok"],
            "budget_ok": budget_ok, "ticket_groks": ticket_groks,
            "control_tie": control_tie, "tickets_aligned": tickets_aligned,
        },
        "p_selected": p_info["selected"], "ticket_grok_count": ticket_count,
        "control_grok_count": control_count,
    }


def build_report(cache: dict, info: dict, generated_at: str | None = None) -> dict:
    rows = []
    for row in cache["arm_p"]["rows"]:
        rows.append({
            "phase": "P", "mode_or_arm": row["mode"], "seed": "", "sparsity": row["sparsity"],
            "heldout_acc": row["heldout_acc"], "known_share": row["known_share"],
            "random_share": row["random_share_mean"], "share_margin": row["share_margin"],
            "top_freqs": ",".join(map(str, row["top_freqs"])), "t_gen": "", "step_cap": "", "grokked": "",
        })
    for row in cache["arm_l"]["rows"]:
        rows.append({
            "phase": "L", "mode_or_arm": row["arm"], "seed": row["seed"], "sparsity": row["sparsity"],
            "heldout_acc": row["heldout_acc"], "known_share": row["known_share"],
            "random_share": "", "share_margin": row["share_gap"],
            "top_freqs": ",".join(map(str, row["top_freqs"])), "t_gen": row["t_gen"],
            "step_cap": row["step_cap"], "grokked": row["grokked"],
        })
    summary = {
        "verdict": info["verdict"], "scope": "toy_scale_own_substrate",
        "checkpoint_sha256": cache["checkpoint_sha_after"],
        "arm_p_probe_ok": info["gates"]["arm_p_probe_ok"],
        "arm_p_aligned": info["gates"]["arm_p_aligned"],
        "ticket_grok_count": info["ticket_grok_count"],
        "control_grok_count": info["control_grok_count"],
        "tickets_aligned": info["gates"]["tickets_aligned"],
        "actual_training_runs": cache["arm_l"]["actual_runs"],
        "max_training_runs": cache["arm_l"]["max_runs"],
        "descoped_levels": cache["arm_l"]["descoped_levels"],
        **info["gates"],
    }
    return {
        "schema_version": 1, "title": "MiniGPT v1275 Fourier lottery-ticket test",
        "description": "Preregistered toy-scale test of whether magnitude pruning preserves the known Fourier circuit.",
        "generated_at": generated_at or utc_now(), "status": info["status"],
        "decision": info["verdict"], "summary": summary, "rows": rows,
        "recommendations": [
            "Interpret this result only on the mod-97 toy model and its frozen v1185 substrate.",
            "The 0.75 and 0.875 IMP levels were pre-run descoped to honor the five-runs-per-seed cap.",
            "Use the cached measurements for threshold re-analysis; do not retrain in Phase B.",
        ],
        "csv_fieldnames": list(rows[0]) if rows else [],
    }


def plot_result(cache: dict, path: str | Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    p_rows = cache["arm_p"]["rows"]
    for mode, marker in (("per_tensor", "o"), ("global", "s")):
        rows = [row for row in p_rows if row["mode"] == mode]
        ax.plot([row["sparsity"] for row in rows], [row["heldout_acc"] for row in rows], marker=marker, label=f"P accuracy: {mode}")
    l_rows = [row for row in cache["arm_l"]["rows"] if row["arm"] != "dense"]
    for arm, marker in (("ticket", "^"), ("random", "x"), ("reinit", "D")):
        rows = [row for row in l_rows if row["arm"] == arm]
        if rows:
            ax.scatter([0.5], [sum(row["heldout_acc"] for row in rows) / len(rows)], marker=marker, s=75, label=f"L mean accuracy: {arm}")
    ax.axhline(0.90, color="black", linestyle="--", linewidth=1, label="accuracy gate 0.90")
    ax.set(xlabel="Sparsity", ylabel="Held-out accuracy", ylim=(-0.02, 1.03), title="v1275: pruning accuracy and Fourier alignment")
    align_ax = ax.twinx()
    global_rows = [row for row in p_rows if row["mode"] == "global"]
    align_ax.plot([row["sparsity"] for row in global_rows], [row["share_margin"] for row in global_rows], color="#b34d00", marker=".", label="P global Fourier margin")
    ticket_rows = [row for row in l_rows if row["arm"] == "ticket"]
    if ticket_rows:
        align_ax.scatter([0.5], [sum(row["share_gap"] for row in ticket_rows) / len(ticket_rows)], color="#6a1b9a", marker="*", s=120, label="L ticket share gap")
    else:
        ax.text(0.72, 0.72, "Arm L not run: 50% probe failed", transform=ax.transAxes, ha="center")
    align_ax.axhline(0.05, color="#b34d00", linestyle=":", linewidth=1, label="P alignment gate")
    align_ax.set_ylabel("Fixed-frequency power margin / gap")
    handles, labels = ax.get_legend_handles_labels()
    other_handles, other_labels = align_ax.get_legend_handles_labels()
    ax.legend(handles + other_handles, labels + other_labels, loc="lower left", fontsize=8)
    fig.tight_layout()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=160)
    plt.close(fig)


__all__ = [
    "CKPT_SHA256", "KNOWN_FREQS", "TicketConfig", "arm_p_result", "build_report", "decide",
    "file_sha256", "freq_stats", "make_mask", "mask_sparsity", "plot_result", "prune_targets",
    "run_arm_l", "run_arm_p", "run_phase_a",
]
