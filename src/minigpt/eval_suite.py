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
    task_type: str = "general"
    difficulty: str = "medium"
    expected_behavior: str = ""
    tags: tuple[str, ...] = ()

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
        if not self.task_type.strip():
            raise ValueError("task_type cannot be empty")
        if not self.difficulty.strip():
            raise ValueError("difficulty cannot be empty")
        raw_tags: Any = self.tags
        if isinstance(raw_tags, str):
            tags = tuple(tag.strip() for tag in raw_tags.split(",") if tag.strip())
        elif raw_tags is None:
            tags = ()
        else:
            tags = tuple(str(tag) for tag in raw_tags if str(tag).strip())
        object.__setattr__(self, "tags", tags)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromptSuite:
    name: str
    version: str = "1"
    description: str = ""
    language: str = "zh-CN"
    cases: tuple[PromptCase, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("prompt suite name cannot be empty")
        if not self.version.strip():
            raise ValueError("prompt suite version cannot be empty")
        if not self.cases:
            raise ValueError("prompt suite requires at least one case")
        object.__setattr__(self, "cases", tuple(self.cases))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "language": self.language,
            "cases": [case.to_dict() for case in self.cases],
        }


@dataclass(frozen=True)
class PromptResult:
    name: str
    prompt: str
    task_type: str
    difficulty: str
    expected_behavior: str
    tags: tuple[str, ...]
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


def default_prompt_suite() -> PromptSuite:
    return PromptSuite(
        name="minigpt-zh-benchmark",
        version="1",
        description="Small fixed Chinese benchmark prompts for MiniGPT learning runs.",
        language="zh-CN",
        cases=(
            PromptCase(
                "continuation-basic",
                "人工智能正在改变",
                max_new_tokens=60,
                temperature=0.7,
                top_k=20,
                seed=101,
                task_type="continuation",
                difficulty="easy",
                expected_behavior="Continue the sentence with coherent Chinese text.",
                tags=("zh", "continuation"),
            ),
            PromptCase(
                "qa-training",
                "问题：什么是模型训练？\n回答：",
                max_new_tokens=70,
                temperature=0.7,
                top_k=25,
                seed=102,
                task_type="qa",
                difficulty="easy",
                expected_behavior="Answer the question briefly and stay on the topic of model training.",
                tags=("zh", "qa", "training"),
            ),
            PromptCase(
                "summary-data-quality",
                "请用一句话总结：数据质量会影响模型训练稳定性、评估可信度和最终生成效果。\n总结：",
                max_new_tokens=70,
                temperature=0.6,
                top_k=25,
                seed=103,
                task_type="summary",
                difficulty="medium",
                expected_behavior="Produce a one-sentence summary that mentions data quality and model outcomes.",
                tags=("zh", "summary", "data"),
            ),
            PromptCase(
                "structured-run-record",
                "请按 JSON 风格列出一次 MiniGPT 实验需要记录的三项信息：",
                max_new_tokens=90,
                temperature=0.6,
                top_k=30,
                seed=104,
                task_type="structured",
                difficulty="medium",
                expected_behavior="Generate a compact structured list with experiment metadata fields.",
                tags=("zh", "structured", "experiment"),
            ),
            PromptCase(
                "consistency-val-loss",
                "判断：如果验证集损失持续上升，模型一定更好吗？请回答原因：",
                max_new_tokens=80,
                temperature=0.7,
                top_k=30,
                seed=105,
                task_type="factual-consistency",
                difficulty="medium",
                expected_behavior="Reject the false premise and explain that rising validation loss is usually worse.",
                tags=("zh", "reasoning", "evaluation"),
            ),
        ),
    )


def default_prompt_cases() -> list[PromptCase]:
    return list(default_prompt_suite().cases)


def load_prompt_suite(path: str | Path | None = None) -> PromptSuite:
    if path is None:
        return default_prompt_suite()
    suite_path = Path(path)
    payload = json.loads(suite_path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        raw_cases = payload.get("cases")
        name = str(payload.get("suite_name") or payload.get("name") or suite_path.stem)
        version = str(payload.get("suite_version") or payload.get("version") or "1")
        description = str(payload.get("description") or "")
        language = str(payload.get("language") or "zh-CN")
    else:
        raw_cases = payload
        name = suite_path.stem
        version = "1"
        description = ""
        language = "zh-CN"
    if not isinstance(raw_cases, list):
        raise ValueError("prompt suite must be a list or an object with a cases list")
    cases = tuple(_case_from_dict(item) for item in raw_cases)
    return PromptSuite(name=name, version=version, description=description, language=language, cases=cases)


def load_prompt_cases(path: str | Path | None = None) -> list[PromptCase]:
    return list(load_prompt_suite(path).cases)


def build_prompt_result(case: PromptCase, generated: str) -> PromptResult:
    continuation = generated[len(case.prompt) :] if generated.startswith(case.prompt) else generated
    return PromptResult(
        name=case.name,
        prompt=case.prompt,
        task_type=case.task_type,
        difficulty=case.difficulty,
        expected_behavior=case.expected_behavior,
        tags=case.tags,
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
    suite_name: str | None = None,
    suite_version: str | None = None,
    suite_description: str | None = None,
    suite_language: str | None = None,
) -> dict[str, Any]:
    if not results:
        raise ValueError("eval suite report requires at least one result")
    task_type_counts = _count_by(result.task_type for result in results)
    difficulty_counts = _count_by(result.difficulty for result in results)
    return {
        "schema_version": 1,
        "checkpoint": checkpoint,
        "tokenizer": tokenizer,
        "suite": suite,
        "benchmark": {
            "suite_name": suite_name,
            "suite_version": suite_version,
            "description": suite_description,
            "language": suite_language,
            "task_type_counts": task_type_counts,
            "difficulty_counts": difficulty_counts,
            "task_type_summary": _summary_by(results, "task_type"),
            "difficulty_summary": _summary_by(results, "difficulty"),
        },
        "case_count": len(results),
        "avg_continuation_chars": round(sum(result.char_count for result in results) / len(results), 4),
        "avg_unique_chars": round(sum(result.unique_char_count for result in results) / len(results), 4),
        "task_type_counts": task_type_counts,
        "difficulty_counts": difficulty_counts,
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
        "task_type",
        "difficulty",
        "prompt",
        "expected_behavior",
        "tags",
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
            row = {field: result.get(field) for field in fieldnames}
            row["tags"] = ",".join(result.get("tags") or [])
            writer.writerow(row)


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
        label = (
            f"{result['name']} [{result.get('task_type', 'general')}/{result.get('difficulty', 'medium')}] "
            f"seed={result['seed']} temp={result['temperature']} top_k={result['top_k'] or 'none'}"
        )
        rows.append(f'<text x="28" y="{y + 18}" font-family="Arial" font-size="13" fill="#111827">{html.escape(label)}</text>')
        rows.append(f'<rect x="{bar_x}" y="{y + 28}" width="{bar}" height="16" rx="3" fill="#7c3aed"/>')
        rows.append(f'<text x="{bar_x + bar + 10}" y="{y + 42}" font-family="Arial" font-size="12" fill="#374151">unique={unique}</text>')
        rows.append(f'<text x="28" y="{y + 48}" font-family="Arial" font-size="12" fill="#4b5563">{html.escape(_clip(str(result.get("continuation", "")), 56))}</text>')
    benchmark = report.get("benchmark") if isinstance(report.get("benchmark"), dict) else {}
    title = benchmark.get("suite_name") or "MiniGPT benchmark eval suite"
    version = benchmark.get("suite_version")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f7f7f2"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">{html.escape(str(title))}</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Version: {html.escape(str(version or 'n/a'))} | Fixed prompts: {report.get('case_count')} | Avg continuation chars: {report.get('avg_continuation_chars')}</text>
  <text x="28" y="76" font-family="Arial" font-size="12" fill="#374151">Purple bars compare unique characters per continuation.</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def render_eval_suite_html(report: dict[str, Any]) -> str:
    benchmark = report.get("benchmark") if isinstance(report.get("benchmark"), dict) else {}
    task_counts = benchmark.get("task_type_counts") or report.get("task_type_counts") or {}
    difficulty_counts = benchmark.get("difficulty_counts") or report.get("difficulty_counts") or {}
    stats = [
        ("Suite", benchmark.get("suite_name") or report.get("suite")),
        ("Version", benchmark.get("suite_version")),
        ("Cases", report.get("case_count")),
        ("Avg chars", report.get("avg_continuation_chars")),
        ("Avg unique", report.get("avg_unique_chars")),
        ("Tasks", _join_counts(task_counts)),
        ("Difficulty", _join_counts(difficulty_counts)),
    ]
    result_rows = []
    for result in report.get("results", []):
        if not isinstance(result, dict):
            continue
        result_rows.append(
            "<tr>"
            f"<td>{_e(result.get('name'))}</td>"
            f"<td>{_e(result.get('task_type'))}</td>"
            f"<td>{_e(result.get('difficulty'))}</td>"
            f"<td>{_e(result.get('seed'))}</td>"
            f"<td>{_e(result.get('unique_char_count'))}</td>"
            f"<td>{_e(_clip(str(result.get('prompt', '')), 44))}</td>"
            f"<td>{_e(_clip(str(result.get('continuation', '')), 72))}</td>"
            f"<td>{_e(_clip(str(result.get('expected_behavior', '')), 72))}</td>"
            "</tr>"
        )
    summary_rows = []
    for item in benchmark.get("task_type_summary") or []:
        if isinstance(item, dict):
            summary_rows.append(
                "<tr>"
                f"<td>{_e(item.get('key'))}</td>"
                f"<td>{_e(item.get('case_count'))}</td>"
                f"<td>{_e(item.get('avg_continuation_chars'))}</td>"
                f"<td>{_e(item.get('avg_unique_chars'))}</td>"
                "</tr>"
            )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(benchmark.get('suite_name') or 'MiniGPT benchmark eval suite')}</title>",
            _html_style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(benchmark.get('suite_name') or 'MiniGPT benchmark eval suite')}</h1><p>{_e(benchmark.get('description') or 'Fixed prompt benchmark report')}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Task Summary</h2><table><thead><tr><th>Task</th><th>Cases</th><th>Avg Chars</th><th>Avg Unique</th></tr></thead><tbody>'
            + "".join(summary_rows)
            + "</tbody></table></section>",
            '<section class="panel"><h2>Prompt Results</h2><table><thead><tr><th>Name</th><th>Task</th><th>Difficulty</th><th>Seed</th><th>Unique</th><th>Prompt</th><th>Continuation</th><th>Expected Behavior</th></tr></thead><tbody>'
            + "".join(result_rows)
            + "</tbody></table></section>",
            "<footer>Generated by MiniGPT eval suite.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_eval_suite_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_eval_suite_html(report), encoding="utf-8")


def write_eval_suite_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "eval_suite.json",
        "csv": root / "eval_suite.csv",
        "svg": root / "eval_suite.svg",
        "html": root / "eval_suite.html",
    }
    write_eval_suite_json(report, paths["json"])
    write_eval_suite_csv(report, paths["csv"])
    write_eval_suite_svg(report, paths["svg"])
    write_eval_suite_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _case_from_dict(payload: Any) -> PromptCase:
    if not isinstance(payload, dict):
        raise ValueError("each prompt case must be an object")
    top_k = payload.get("top_k", 30)
    if top_k in {"", 0, "0", "none", "None", None}:
        top_k = None
    raw_tags = payload.get("tags", ())
    tags = tuple(raw_tags) if isinstance(raw_tags, list) else tuple(str(raw_tags).split(",")) if raw_tags else ()
    return PromptCase(
        name=str(payload["name"]),
        prompt=str(payload["prompt"]),
        max_new_tokens=int(payload.get("max_new_tokens", 60)),
        temperature=float(payload.get("temperature", 0.8)),
        top_k=None if top_k is None else int(top_k),
        seed=int(payload.get("seed", 42)),
        task_type=str(payload.get("task_type") or "general"),
        difficulty=str(payload.get("difficulty") or "medium"),
        expected_behavior=str(payload.get("expected_behavior") or ""),
        tags=tags,
    )


def _clip(text: str, limit: int) -> str:
    flat = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "..."


def _count_by(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _summary_by(results: list[PromptResult], attribute: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[PromptResult]] = {}
    for result in results:
        key = str(getattr(result, attribute) or "unknown")
        buckets.setdefault(key, []).append(result)
    summaries = []
    for key in sorted(buckets):
        items = buckets[key]
        summaries.append(
            {
                "key": key,
                "case_count": len(items),
                "avg_continuation_chars": _avg(result.char_count for result in items),
                "avg_unique_chars": _avg(result.unique_char_count for result in items),
            }
        )
    return summaries


def _avg(values: Any) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(items) / len(items), 4)


def _join_counts(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return ""
    return ", ".join(f"{key}={count}" for key, count in value.items())


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _stat(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e(value)}</div></div>'


def _html_style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee8; --page:#f6f8fb; --panel:#ffffff; --accent:#2563eb; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:30px 36px 18px; background:#ffffff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 14px; font-size:20px; letter-spacing:0; }
p { margin:0; color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; padding:18px 36px 0; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
.card { padding:14px 16px; min-height:74px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:16px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 36px; padding:18px; overflow:auto; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th, td { padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:#1f2937; background:#eef2f7; font-weight:700; }
footer { padding:12px 36px 28px; color:var(--muted); font-size:12px; }
</style>"""
