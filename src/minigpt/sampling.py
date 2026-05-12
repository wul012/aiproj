from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import html
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SamplingCase:
    name: str
    temperature: float
    top_k: int | None
    seed: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("sampling case name cannot be empty")
        if self.temperature <= 0:
            raise ValueError("temperature must be greater than 0")
        if self.top_k is not None and self.top_k < 1:
            raise ValueError("top_k must be at least 1 when provided")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SamplingResult:
    name: str
    temperature: float
    top_k: int | None
    seed: int
    prompt: str
    max_new_tokens: int
    generated: str
    continuation: str
    char_count: int
    unique_char_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_sampling_cases() -> list[SamplingCase]:
    return [
        SamplingCase("conservative", temperature=0.6, top_k=10, seed=11),
        SamplingCase("balanced", temperature=0.8, top_k=30, seed=22),
        SamplingCase("creative", temperature=1.1, top_k=None, seed=33),
    ]


def parse_sampling_case(spec: str) -> SamplingCase:
    parts = [part.strip() for part in spec.split(":")]
    if len(parts) != 4:
        raise ValueError("sampling case must use name:temperature:top_k:seed")
    name, temperature_text, top_k_text, seed_text = parts
    top_k = None if top_k_text in {"", "0", "none", "None"} else int(top_k_text)
    return SamplingCase(
        name=name,
        temperature=float(temperature_text),
        top_k=top_k,
        seed=int(seed_text),
    )


def continuation_from_generated(generated: str, prompt: str) -> str:
    if generated.startswith(prompt):
        return generated[len(prompt) :]
    return generated


def build_sampling_result(
    case: SamplingCase,
    prompt: str,
    max_new_tokens: int,
    generated: str,
) -> SamplingResult:
    if max_new_tokens < 1:
        raise ValueError("max_new_tokens must be at least 1")
    continuation = continuation_from_generated(generated, prompt)
    return SamplingResult(
        name=case.name,
        temperature=case.temperature,
        top_k=case.top_k,
        seed=case.seed,
        prompt=prompt,
        max_new_tokens=max_new_tokens,
        generated=generated,
        continuation=continuation,
        char_count=len(continuation),
        unique_char_count=len(set(continuation)),
    )


def build_sampling_report(
    prompt: str,
    max_new_tokens: int,
    results: list[SamplingResult],
    checkpoint: str | None = None,
    tokenizer: str | None = None,
) -> dict[str, Any]:
    if not results:
        raise ValueError("sampling report requires at least one result")
    return {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "checkpoint": checkpoint,
        "tokenizer": tokenizer,
        "results": [result.to_dict() for result in results],
    }


def write_sampling_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_sampling_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "temperature",
        "top_k",
        "seed",
        "max_new_tokens",
        "char_count",
        "unique_char_count",
        "continuation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in report["results"]:
            writer.writerow({field: result.get(field) for field in fieldnames})


def write_sampling_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = list(report["results"])
    width = 980
    row_h = 58
    top = 90
    height = top + row_h * len(results) + 54
    bar_x = 230
    bar_w = 480
    max_unique = max((int(result["unique_char_count"]) for result in results), default=1)
    rows: list[str] = []
    for i, result in enumerate(results):
        y = top + i * row_h
        unique = int(result["unique_char_count"])
        bar = 0 if max_unique == 0 else max(2, int(bar_w * unique / max_unique))
        label = f"{result['name']}  temp={result['temperature']} top_k={result['top_k'] or 'none'} seed={result['seed']}"
        snippet = _clip(str(result.get("continuation", "")), limit=42)
        rows.append(f'<text x="28" y="{y + 18}" font-family="Arial" font-size="13" fill="#111827">{html.escape(label)}</text>')
        rows.append(f'<rect x="{bar_x}" y="{y + 28}" width="{bar}" height="16" rx="3" fill="#2563eb"/>')
        rows.append(f'<text x="{bar_x + bar + 10}" y="{y + 42}" font-family="Arial" font-size="12" fill="#374151">unique={unique}</text>')
        rows.append(f'<text x="28" y="{y + 44}" font-family="Arial" font-size="12" fill="#4b5563">{html.escape(snippet)}</text>')

    prompt = html.escape(str(report.get("prompt", "")))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfbf7"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">MiniGPT sampling lab</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Prompt: {prompt}</text>
  <text x="28" y="76" font-family="Arial" font-size="12" fill="#374151">Blue bars compare unique characters in each continuation.</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def write_sampling_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "sample_lab.json",
        "csv": root / "sample_lab.csv",
        "svg": root / "sample_lab.svg",
    }
    write_sampling_json(report, paths["json"])
    write_sampling_csv(report, paths["csv"])
    write_sampling_svg(report, paths["svg"])
    return {key: str(value) for key, value in paths.items()}


def _clip(text: str, limit: int) -> str:
    flat = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "..."
