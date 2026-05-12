from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import html
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PromptCase:
    name: str
    prompt: str
    max_new_tokens: int = 60
    temperature: float = 0.8
    top_k: int | None = 30
    seed: int = 42

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("prompt case name cannot be empty")
        if not self.prompt:
            raise ValueError("prompt cannot be empty")
        if self.max_new_tokens < 1:
            raise ValueError("max_new_tokens must be at least 1")
        if self.temperature <= 0:
            raise ValueError("temperature must be greater than 0")
        if self.top_k is not None and self.top_k < 1:
            raise ValueError("top_k must be at least 1 when provided")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromptResult:
    name: str
    prompt: str
    max_new_tokens: int
    temperature: float
    top_k: int | None
    seed: int
    generated: str
    continuation: str
    char_count: int
    unique_char_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_prompt_cases() -> list[PromptCase]:
    return [
        PromptCase("concept", "人工智能", max_new_tokens=50, temperature=0.7, top_k=20, seed=101),
        PromptCase("training", "模型训练", max_new_tokens=50, temperature=0.8, top_k=30, seed=102),
        PromptCase("data", "数据质量", max_new_tokens=50, temperature=0.9, top_k=30, seed=103),
    ]


def load_prompt_cases(path: str | Path | None = None) -> list[PromptCase]:
    if path is None:
        return default_prompt_cases()
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise ValueError("prompt suite must be a list or an object with a cases list")
    cases = [_case_from_dict(item) for item in raw_cases]
    if not cases:
        raise ValueError("prompt suite requires at least one case")
    return cases


def build_prompt_result(case: PromptCase, generated: str) -> PromptResult:
    continuation = generated[len(case.prompt) :] if generated.startswith(case.prompt) else generated
    return PromptResult(
        name=case.name,
        prompt=case.prompt,
        max_new_tokens=case.max_new_tokens,
        temperature=case.temperature,
        top_k=case.top_k,
        seed=case.seed,
        generated=generated,
        continuation=continuation,
        char_count=len(continuation),
        unique_char_count=len(set(continuation)),
    )


def build_eval_suite_report(
    results: list[PromptResult],
    *,
    checkpoint: str | None = None,
    tokenizer: str | None = None,
    suite: str | None = None,
) -> dict[str, Any]:
    if not results:
        raise ValueError("eval suite report requires at least one result")
    return {
        "schema_version": 1,
        "checkpoint": checkpoint,
        "tokenizer": tokenizer,
        "suite": suite,
        "case_count": len(results),
        "avg_continuation_chars": round(sum(result.char_count for result in results) / len(results), 4),
        "avg_unique_chars": round(sum(result.unique_char_count for result in results) / len(results), 4),
        "results": [result.to_dict() for result in results],
    }


def write_eval_suite_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_eval_suite_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "prompt",
        "max_new_tokens",
        "temperature",
        "top_k",
        "seed",
        "char_count",
        "unique_char_count",
        "continuation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in report["results"]:
            writer.writerow({field: result.get(field) for field in fieldnames})


def write_eval_suite_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = list(report["results"])
    width = 980
    row_h = 64
    top = 92
    height = top + row_h * len(results) + 54
    bar_x = 240
    bar_w = 470
    max_unique = max((int(result["unique_char_count"]) for result in results), default=1)
    rows = []
    for index, result in enumerate(results):
        y = top + index * row_h
        unique = int(result["unique_char_count"])
        bar = 0 if max_unique == 0 else max(2, int(bar_w * unique / max_unique))
        label = f"{result['name']} seed={result['seed']} temp={result['temperature']} top_k={result['top_k'] or 'none'}"
        rows.append(f'<text x="28" y="{y + 18}" font-family="Arial" font-size="13" fill="#111827">{html.escape(label)}</text>')
        rows.append(f'<rect x="{bar_x}" y="{y + 28}" width="{bar}" height="16" rx="3" fill="#7c3aed"/>')
        rows.append(f'<text x="{bar_x + bar + 10}" y="{y + 42}" font-family="Arial" font-size="12" fill="#374151">unique={unique}</text>')
        rows.append(f'<text x="28" y="{y + 48}" font-family="Arial" font-size="12" fill="#4b5563">{html.escape(_clip(str(result.get("continuation", "")), 56))}</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f7f7f2"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">MiniGPT eval suite</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Fixed prompts: {report.get('case_count')} | Avg continuation chars: {report.get('avg_continuation_chars')}</text>
  <text x="28" y="76" font-family="Arial" font-size="12" fill="#374151">Purple bars compare unique characters per continuation.</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def write_eval_suite_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "eval_suite.json",
        "csv": root / "eval_suite.csv",
        "svg": root / "eval_suite.svg",
    }
    write_eval_suite_json(report, paths["json"])
    write_eval_suite_csv(report, paths["csv"])
    write_eval_suite_svg(report, paths["svg"])
    return {key: str(value) for key, value in paths.items()}


def _case_from_dict(payload: Any) -> PromptCase:
    if not isinstance(payload, dict):
        raise ValueError("each prompt case must be an object")
    top_k = payload.get("top_k", 30)
    if top_k in {"", 0, "0", "none", "None", None}:
        top_k = None
    return PromptCase(
        name=str(payload["name"]),
        prompt=str(payload["prompt"]),
        max_new_tokens=int(payload.get("max_new_tokens", 60)),
        temperature=float(payload.get("temperature", 0.8)),
        top_k=None if top_k is None else int(top_k),
        seed=int(payload.get("seed", 42)),
    )


def _clip(text: str, limit: int) -> str:
    flat = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "..."
