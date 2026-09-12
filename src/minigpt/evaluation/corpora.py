"""Named corpus comparisons with explicit aggregation and visible regressions."""

from __future__ import annotations

import html
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from minigpt.evaluation.paired import loss_summary, render_pair


@dataclass(frozen=True)
class Corpus:
    name: str
    path: Path
    weight: float


def load_corpora(path: Path) -> list[Corpus]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict) or type(payload.get("version")) is not int or payload["version"] != 1:
        raise ValueError("Expected corpus manifest version 1")
    rows = payload.get("corpora")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Corpus manifest requires a nonempty corpora list")
    result: list[Corpus] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) - {"name", "path", "weight"}:
            raise ValueError("Invalid corpus entry fields")
        name, source, weight = row.get("name"), row.get("path"), row.get("weight", 1)
        if not isinstance(name, str) or not name.strip() or not isinstance(source, str) or not source.strip():
            raise ValueError("Corpus name and path must be nonempty strings")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise ValueError("Corpus weight must be finite and positive")
        try:
            number = float(weight)
        except OverflowError as exc:
            raise ValueError("Corpus weight exceeds the supported numeric range") from exc
        if not math.isfinite(number) or number <= 0:
            raise ValueError("Corpus weight must be finite and positive")
        corpus = Corpus(name.strip(), (path.parent / source).resolve(), number)
        if any(corpus.name == item.name or corpus.path == item.path for item in result):
            raise ValueError("Corpus names and resolved paths must be unique")
        result.append(corpus)
    return result


def aggregate_corpora(groups: list[dict[str, Any]]) -> dict[str, Any]:
    if not groups:
        raise ValueError("Cannot compare an empty corpus set")
    weights = [float(group["weight"]) for group in groups]
    if not all(math.isfinite(value) and value > 0 for value in weights):
        raise ValueError("Expected finite positive corpus weights")
    largest = max(weights)
    scaled = [value / largest for value in weights]
    totals: dict[str, dict[str, Any]] = {"macro": {}, "weighted": {}}
    for model in ("baseline", "candidate"):
        losses = [float(group["report"]["comparison"][model]["loss"]) for group in groups]
        totals["macro"][model] = loss_summary(losses)
        mean = math.fsum(value * weight for value, weight in zip(losses, scaled)) / math.fsum(scaled)
        totals["weighted"][model] = loss_summary([mean])
    for summary in totals.values():
        summary["delta_loss"] = summary["candidate"]["loss"] - summary["baseline"]["loss"]
    regressed = [group["name"] for group in groups if group["report"]["comparison"]["delta_loss"] > 1e-6]
    return {
        "protocol": "named_corpora_v1",
        "corpora": groups,
        **totals,
        "regressed_corpora": regressed,
        "weighted_gain_with_regressions": totals["weighted"]["delta_loss"] < -1e-6 and bool(regressed),
        "aggregation": "Macro: equal corpus weight. Weighted: declared positive weights applied to corpus mean NLL, not perplexity or observed token counts.",
        "interpretation": "Same paired windows within each corpus; no cross-corpus concatenation. Declared weights are policy, not measured traffic. Overlapping windows are correlated; holdout provenance/significance are not verified.",
    }


def _label(value: str) -> str:
    return html.escape(value).replace("|", "&#124;").replace("`", "&#96;").replace("\n", " ").replace("\r", " ")


def render_corpora(report: dict[str, Any]) -> str:
    lines = [
        "# Per-corpus checkpoint comparison",
        "",
        report["aggregation"],
        "",
        report["interpretation"],
        "",
        "| Corpus | Weight | Windows | Baseline NLL | Candidate NLL | Delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in report["corpora"]:
        row = group["report"]["comparison"]
        lines.append(
            f"| {_label(group['name'])} | {group['weight']:g} | {len(row['windows'])} | {row['baseline']['loss']:.6f} | {row['candidate']['loss']:.6f} | {row['delta_loss']:+.6f} |"
        )
    lines.append("")
    for key, label in (("macro", "Equal-corpus macro"), ("weighted", "Declared-weighted")):
        row = report[key]
        lines.append(
            f"- {label} NLL: {row['baseline']['loss']:.6f} → {row['candidate']['loss']:.6f}; delta {row['delta_loss']:+.6f}."
        )
        lines.append(f"  Perplexity: {row['baseline']['perplexity']} → {row['candidate']['perplexity']}.")
    names = ", ".join(_label(name) for name in report["regressed_corpora"]) or "None"
    lines += [f"- Regressed corpora: {names}."]
    if report["weighted_gain_with_regressions"]:
        lines += [
            "",
            "**Weighted total improves, but at least one corpus regresses. Do not hide this behind the total.**",
        ]
    for group in report["corpora"]:
        lines += [
            "",
            "---",
            "",
            f"## Corpus: {_label(group['name'])}",
            "",
            render_pair(group["report"])
            .replace("\n## ", "\n#### ")
            .replace("# Paired checkpoint evaluation", "### Paired windows", 1),
        ]
    return "\n".join(lines)
