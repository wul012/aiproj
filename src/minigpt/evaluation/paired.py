"""Paired NLL summaries with inspectable improved/regressed text windows."""

from __future__ import annotations

import math
import statistics
from typing import Any

import torch

from minigpt.core.tokenizer import Tokenizer
from minigpt.evaluation.prediction import perplexity_from_loss
from minigpt.evaluation.windows import WindowPlan


def loss_summary(losses: list[float]) -> dict[str, float | None]:
    if not losses or not all(math.isfinite(value) for value in losses):
        raise ValueError("Expected nonempty finite window losses")
    loss = statistics.fmean(losses)
    perplexity = perplexity_from_loss(loss)
    return {"loss": loss, "perplexity": perplexity if math.isfinite(perplexity) else None}


def pair_results(
    baseline: list[float],
    candidate: list[float],
    plan: WindowPlan,
    data: torch.Tensor,
    tokenizer: Tokenizer,
    offset: int,
) -> dict[str, Any]:
    if len(baseline) != len(candidate) or len(baseline) != len(plan.starts):
        raise ValueError("Both models must score every planned window")
    a, b = loss_summary(baseline), loss_summary(candidate)
    rows: list[dict[str, Any]] = []
    tolerance = 1e-6
    for start, before, after in zip(plan.starts, baseline, candidate):
        rows.append(
            {
                "start_token": start + offset,
                "target_end_token": start + offset + plan.context,
                "baseline_loss": before,
                "candidate_loss": after,
                "delta": after - before,
                "input_preview": tokenizer.decode(data[start : start + plan.context].tolist())[:160],
                "target_preview": tokenizer.decode(data[start + 1 : start + plan.context + 1].tolist())[:160],
            }
        )
    improved = sorted((r for r in rows if r["delta"] < -tolerance), key=lambda r: r["delta"])
    regressed = sorted((r for r in rows if r["delta"] > tolerance), key=lambda r: -r["delta"])
    return {
        "baseline": a,
        "candidate": b,
        "delta_loss": statistics.fmean(candidate) - statistics.fmean(baseline),
        "improved_windows": len(improved),
        "regressed_windows": len(regressed),
        "tied_windows": len(rows) - len(improved) - len(regressed),
        "tie_tolerance": tolerance,
        "largest_improvements": improved[:5],
        "largest_regressions": regressed[:5],
        "windows": rows,
    }


def render_pair(report: dict[str, Any]) -> str:
    result, plan = report["comparison"], report["sampling"]
    lines = [
        "# Paired checkpoint evaluation",
        "",
        report["interpretation"],
        "",
        f"Protocol: {plan['protocol']}; context: {plan['context']}; windows: {len(plan['starts'])}; seed: {plan['seed']}",
        "",
        "| Model | Mean NLL (nats/token) | Perplexity |",
        "| --- | ---: | ---: |",
    ]
    for name in ("baseline", "candidate"):
        row = result[name]
        ppl = f"{row['perplexity']:.6f}" if row["perplexity"] is not None else "overflow (null)"
        lines.append(f"| {name} | {row['loss']:.8f} | {ppl} |")
    lines += [
        "",
        f"Candidate - baseline NLL: {result['delta_loss']:+.8f} (negative is better on these windows).",
        f"Improved / regressed / tied: {result['improved_windows']} / {result['regressed_windows']} / {result['tied_windows']}",
        f"Unknown tokens in evaluation split: {report['unknown_tokens']}",
        "",
    ]
    for key, title in (
        ("largest_improvements", "Largest improvements"),
        ("largest_regressions", "Largest regressions"),
    ):
        lines += [f"## {title}", ""]
        for row in result[key]:
            preview = row["target_preview"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            preview = preview.replace("\n", " ").replace("\r", " ").replace("`", "&#96;")
            lines.append(f"- Token {row['start_token']}: Δ {row['delta']:+.6f}; target `{preview}`")
        if not result[key]:
            lines.append("- None beyond the numerical tie tolerance.")
        lines.append("")
    return "\n".join(lines)
