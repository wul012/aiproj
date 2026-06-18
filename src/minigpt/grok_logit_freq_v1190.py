"""v1190: align embedding frequencies with output-logit frequencies.

v1188 showed that the grokked checkpoint's number embeddings are Fourier
concentrated. This follow-up checks the other side of the trig-identity story:
the output logits over all prompts ``[a,+,b,=]`` should also organize around the
same frequencies. For an ideal modular-addition score surface, each output-logit
slice is a ridge ``a+b=y``; its 2D FFT over ``(a,b)`` has power only where the two
input frequencies are equal. A real grokked model should have high diagonal FFT
power and its dominant folded diagonal frequencies should overlap the embedding
dominant frequencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from minigpt.grok_checkpoint_v1185 import CheckpointMeta, load_checkpoint
from minigpt.grok_interp_v1188 import TOP_K, analyze_model
from minigpt.grok_predict_v1186 import DEFAULT_CHECKPOINT, evaluate_table
from minigpt.grok_v1179 import GrokConfig, make_grok_model
from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import utc_now
from minigpt.script_runtime import seed_everything

GROK_LOGIT_FREQ_STEM = "grok_logit_freq_v1190"


def prompt_grid(p: int, device: torch.device | None = None) -> torch.Tensor:
    rows = [[a, p, b, p + 1] for a in range(p) for b in range(p)]
    return torch.tensor(rows, dtype=torch.long, device=device)


@torch.no_grad()
def answer_logit_cube(model: torch.nn.Module, p: int) -> torch.Tensor:
    model.eval()
    device = next(model.parameters()).device
    logits, _ = model(prompt_grid(p, device=device))
    return logits[:, -1, :p].reshape(p, p, p).detach().cpu().float()


def ideal_addition_cube(p: int) -> torch.Tensor:
    cube = torch.zeros((p, p, p), dtype=torch.float32)
    for a in range(p):
        for b in range(p):
            cube[a, b, (a + b) % p] = 1.0
    return cube


def diagonal_fft_power(cube: torch.Tensor) -> torch.Tensor:
    centered = cube.float() - cube.float().mean(dim=(0, 1), keepdim=True)
    spectrum = torch.fft.fft2(centered, dim=(0, 1))
    power = (spectrum.abs() ** 2).sum(dim=2)
    power[0, 0] = 0.0
    return power


def fold_frequency(freq: int, p: int) -> int:
    freq = int(freq) % p
    return min(freq, p - freq)


def folded_diagonal_distribution(power: torch.Tensor, p: int) -> list[dict[str, float | int]]:
    diag = torch.diag(power)
    folded: dict[int, float] = {}
    for raw_freq in range(1, p):
        folded_freq = fold_frequency(raw_freq, p)
        folded[folded_freq] = folded.get(folded_freq, 0.0) + float(diag[raw_freq])
    total = sum(folded.values())
    return [
        {"freq": freq, "fraction": (value / total if total > 0 else 0.0)}
        for freq, value in sorted(folded.items())
    ]


def logit_frequency_metrics(cube: torch.Tensor, p: int, top_k: int = TOP_K) -> dict[str, Any]:
    power = diagonal_fft_power(cube)
    total_power = float(power.sum())
    diag_power = float(torch.diag(power).sum())
    distribution = folded_diagonal_distribution(power, p)
    ranked = sorted(distribution, key=lambda row: float(row["fraction"]), reverse=True)
    top = ranked[:top_k]
    return {
        "diagonal_fraction": round(diag_power / total_power, 6) if total_power > 0 else 0.0,
        "top_k_diagonal_fraction": round(sum(float(row["fraction"]) for row in top), 6),
        "dominant_freq": int(top[0]["freq"]) if top else None,
        "top_freqs": [int(row["freq"]) for row in top],
        "folded_diagonal_distribution": [
            {"freq": int(row["freq"]), "fraction": round(float(row["fraction"]), 6)}
            for row in distribution
        ],
    }


def make_random_like(meta: CheckpointMeta, device: torch.device) -> torch.nn.Module:
    seed_everything(meta.seed)
    config = GrokConfig(
        p=meta.p,
        train_frac=meta.train_frac,
        n_layer=meta.n_layer,
        n_head=meta.n_head,
        n_embd=meta.n_embd,
        seeds=(meta.seed,),
        wds=(meta.weight_decay,),
    )
    return make_grok_model(meta.vocab_size, config).to(device)


def frequency_overlap(left: list[int], right: list[int]) -> dict[str, Any]:
    left_set = set(int(item) for item in left)
    right_set = set(int(item) for item in right)
    overlap = sorted(left_set & right_set)
    denom = max(1, min(len(left_set), len(right_set)))
    return {"count": len(overlap), "fraction": round(len(overlap) / denom, 6), "freqs": overlap}


def decide_alignment(
    *,
    table: dict[str, Any],
    embedding_metrics: dict[str, Any],
    shipped_logit: dict[str, Any],
    random_logit: dict[str, Any],
    ideal_logit: dict[str, Any],
    min_heldout_acc: float = 0.90,
    min_diagonal_fraction: float = 0.50,
    min_diagonal_gap: float = 0.25,
    min_top_overlap: int = 4,
) -> dict[str, Any]:
    overlap = frequency_overlap(list(embedding_metrics["top_freqs"]), list(shipped_logit["top_freqs"]))
    checks = [
        _check("checkpoint_generalizes", table["heldout_acc"] >= min_heldout_acc, f">= {min_heldout_acc}", table["heldout_acc"]),
        _check("ideal_addition_is_diagonal", ideal_logit["diagonal_fraction"] >= 0.999, ">= 0.999", ideal_logit["diagonal_fraction"]),
        _check(
            "shipped_logits_have_diagonal_frequency_structure",
            shipped_logit["diagonal_fraction"] >= min_diagonal_fraction,
            f">= {min_diagonal_fraction}",
            shipped_logit["diagonal_fraction"],
        ),
        _check(
            "random_logits_are_not_diagonal",
            random_logit["diagonal_fraction"] <= 0.05,
            "<= 0.05",
            random_logit["diagonal_fraction"],
        ),
        _check(
            "diagonal_gap_is_large",
            (shipped_logit["diagonal_fraction"] - random_logit["diagonal_fraction"]) >= min_diagonal_gap,
            f">= {min_diagonal_gap}",
            round(shipped_logit["diagonal_fraction"] - random_logit["diagonal_fraction"], 6),
        ),
        _check(
            "embedding_logit_top_freqs_overlap",
            overlap["count"] >= min_top_overlap,
            f">= {min_top_overlap}",
            overlap,
        ),
        _check(
            "dominant_frequency_matches",
            embedding_metrics["dominant_freq"] == shipped_logit["dominant_freq"],
            embedding_metrics["dominant_freq"],
            shipped_logit["dominant_freq"],
        ),
    ]
    failed = [row for row in checks if row["status"] != "pass"]
    if not failed:
        decision = "embedding_logit_frequency_alignment_supports_trig_addition"
    elif shipped_logit["diagonal_fraction"] >= min_diagonal_fraction:
        decision = "logit_diagonal_structure_present_but_embedding_alignment_incomplete"
    else:
        decision = "logit_frequency_alignment_not_supported"
    return {"status": "pass" if not failed else "review", "decision": decision, "checks": checks, "failed": failed, "overlap": overlap}


def build_report(
    *,
    checkpoint_path: str | Path = DEFAULT_CHECKPOINT,
    device: torch.device | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    device = device or torch.device("cpu")
    model, meta = load_checkpoint(checkpoint_path, device=device)
    table = evaluate_table(model, meta)
    embedding_metrics = analyze_model(model, meta.p)
    shipped_logit = logit_frequency_metrics(answer_logit_cube(model, meta.p), meta.p)
    random_model = make_random_like(meta, device)
    random_logit = logit_frequency_metrics(answer_logit_cube(random_model, meta.p), meta.p)
    ideal_logit = logit_frequency_metrics(ideal_addition_cube(meta.p), meta.p)
    alignment = decide_alignment(
        table=table,
        embedding_metrics=embedding_metrics,
        shipped_logit=shipped_logit,
        random_logit=random_logit,
        ideal_logit=ideal_logit,
    )
    rows = [
        _row("shipped_checkpoint_logits", shipped_logit),
        _row("random_init_logits", random_logit),
        _row("ideal_addition_target", ideal_logit),
    ]
    summary = {
        "checkpoint": str(checkpoint_path),
        "p": meta.p,
        "heldout_acc": table["heldout_acc"],
        "embedding_top_freqs": embedding_metrics["top_freqs"],
        "embedding_top_k_fraction": embedding_metrics["top_k_fraction"],
        "embedding_dominant_freq": embedding_metrics["dominant_freq"],
        "logit_top_freqs": shipped_logit["top_freqs"],
        "logit_top_k_diagonal_fraction": shipped_logit["top_k_diagonal_fraction"],
        "logit_diagonal_fraction": shipped_logit["diagonal_fraction"],
        "random_logit_diagonal_fraction": random_logit["diagonal_fraction"],
        "ideal_logit_diagonal_fraction": ideal_logit["diagonal_fraction"],
        "embedding_logit_top_freq_overlap_count": alignment["overlap"]["count"],
        "embedding_logit_top_freq_overlap_fraction": alignment["overlap"]["fraction"],
        "embedding_logit_top_freq_overlap": alignment["overlap"]["freqs"],
        "boundary": "toy_scale_single_checkpoint_embedding_logit_frequency_alignment_not_a_scaling_claim",
    }
    return {
        "schema_version": 1,
        "title": "MiniGPT v1190 grokking logit-frequency alignment",
        "generated_at": generated_at or utc_now(),
        "status": alignment["status"],
        "decision": alignment["decision"],
        "summary": summary,
        "rows": rows,
        "check_rows": alignment["checks"],
        "issues": alignment["failed"],
        "distributions": {
            "shipped_checkpoint_logits": shipped_logit["folded_diagonal_distribution"],
            "random_init_logits": random_logit["folded_diagonal_distribution"],
            "ideal_addition_target": ideal_logit["folded_diagonal_distribution"],
        },
        "recommendations": _recommendations(alignment["decision"], summary),
        "csv_fieldnames": ["arm", "diagonal_fraction", "top_k_diagonal_fraction", "dominant_freq", "top_freqs"],
    }


def write_grok_logit_freq_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=GROK_LOGIT_FREQ_STEM, row_title="Logit Frequency Arms")


def _row(name: str, metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "arm": name,
        "diagonal_fraction": metrics["diagonal_fraction"],
        "top_k_diagonal_fraction": metrics["top_k_diagonal_fraction"],
        "dominant_freq": metrics["dominant_freq"],
        "top_freqs": ", ".join(str(freq) for freq in metrics["top_freqs"]),
    }


def _check(check_id: str, passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "expected": expected, "actual": actual}


def _recommendations(decision: str, summary: dict[str, Any]) -> list[str]:
    if decision == "embedding_logit_frequency_alignment_supports_trig_addition":
        return [
            "The shipped grokking checkpoint's output logits are concentrated on the diagonal 2D FFT frequencies expected for a+b=y modular addition surfaces.",
            f"The logit dominant frequencies {summary['logit_top_freqs']} align with the embedding dominant frequencies {summary['embedding_top_freqs']}, supporting the trig-identity mechanism behind v1188.",
        ]
    return [
        "Do not cite output-logit frequency alignment as mechanistic support until every check row passes.",
        "Inspect the diagonal FFT fraction first, then the embedding/logit frequency overlap.",
    ]


__all__ = [
    "GROK_LOGIT_FREQ_STEM",
    "answer_logit_cube",
    "build_report",
    "decide_alignment",
    "diagonal_fft_power",
    "fold_frequency",
    "folded_diagonal_distribution",
    "frequency_overlap",
    "ideal_addition_cube",
    "logit_frequency_metrics",
    "make_random_like",
    "prompt_grid",
    "write_grok_logit_freq_outputs",
]
