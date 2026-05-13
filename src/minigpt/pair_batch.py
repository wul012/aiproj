from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
import html
import json
from pathlib import Path
from typing import Any

from .eval_suite import PromptCase, PromptSuite


def build_pair_batch_case_result(
    case: PromptCase,
    left_response: Any,
    right_response: Any,
    *,
    left_checkpoint_id: str = "left",
    right_checkpoint_id: str = "right",
) -> dict[str, Any]:
    left = _response_payload(left_response, left_checkpoint_id)
    right = _response_payload(right_response, right_checkpoint_id)
    left_generated = str(left.get("generated") or "")
    right_generated = str(right.get("generated") or "")
    left_continuation = str(left.get("continuation") or "")
    right_continuation = str(right.get("continuation") or "")
    left_generated_chars = len(left_generated)
    right_generated_chars = len(right_generated)
    left_continuation_chars = len(left_continuation)
    right_continuation_chars = len(right_continuation)
    return {
        "name": case.name,
        "prompt": case.prompt,
        "task_type": case.task_type,
        "difficulty": case.difficulty,
        "expected_behavior": case.expected_behavior,
        "tags": list(case.tags),
        "max_new_tokens": case.max_new_tokens,
        "temperature": case.temperature,
        "top_k": case.top_k,
        "seed": case.seed,
        "left": {
            **left,
            "generated_chars": left_generated_chars,
            "continuation_chars": left_continuation_chars,
            "unique_continuation_chars": len(set(left_continuation)),
        },
        "right": {
            **right,
            "generated_chars": right_generated_chars,
            "continuation_chars": right_continuation_chars,
            "unique_continuation_chars": len(set(right_continuation)),
        },
        "comparison": {
            "same_checkpoint": left_checkpoint_id == right_checkpoint_id,
            "generated_equal": left_generated == right_generated,
            "continuation_equal": left_continuation == right_continuation,
            "left_generated_chars": left_generated_chars,
            "right_generated_chars": right_generated_chars,
            "generated_char_delta": right_generated_chars - left_generated_chars,
            "left_continuation_chars": left_continuation_chars,
            "right_continuation_chars": right_continuation_chars,
            "continuation_char_delta": right_continuation_chars - left_continuation_chars,
            "left_unique_continuation_chars": len(set(left_continuation)),
            "right_unique_continuation_chars": len(set(right_continuation)),
            "unique_continuation_char_delta": len(set(right_continuation)) - len(set(left_continuation)),
        },
    }


def build_pair_batch_report(
    results: list[dict[str, Any]],
    *,
    suite: PromptSuite | None = None,
    suite_path: str | Path | None = None,
    left_checkpoint: str | Path | None = None,
    right_checkpoint: str | Path | None = None,
    left_checkpoint_id: str = "left",
    right_checkpoint_id: str = "right",
    left_tokenizer: str | Path | None = None,
    right_tokenizer: str | Path | None = None,
) -> dict[str, Any]:
    if not results:
        raise ValueError("pair batch report requires at least one result")
    comparisons = [_pick_dict(result, "comparison") for result in results]
    task_type_counts = _count_by(result.get("task_type") for result in results)
    difficulty_counts = _count_by(result.get("difficulty") for result in results)
    generated_equal_count = sum(1 for item in comparisons if item.get("generated_equal") is True)
    continuation_equal_count = sum(1 for item in comparisons if item.get("continuation_equal") is True)
    return {
        "schema_version": 1,
        "kind": "minigpt_pair_generation_batch",
        "suite": {
            "name": suite.name if suite is not None else None,
            "version": suite.version if suite is not None else None,
            "description": suite.description if suite is not None else None,
            "language": suite.language if suite is not None else None,
            "path": str(suite_path) if suite_path is not None else None,
        },
        "left": {
            "checkpoint_id": left_checkpoint_id,
            "checkpoint": str(left_checkpoint) if left_checkpoint is not None else None,
            "tokenizer": str(left_tokenizer) if left_tokenizer is not None else None,
        },
        "right": {
            "checkpoint_id": right_checkpoint_id,
            "checkpoint": str(right_checkpoint) if right_checkpoint is not None else None,
            "tokenizer": str(right_tokenizer) if right_tokenizer is not None else None,
        },
        "case_count": len(results),
        "generated_equal_count": generated_equal_count,
        "continuation_equal_count": continuation_equal_count,
        "generated_difference_count": len(results) - generated_equal_count,
        "continuation_difference_count": len(results) - continuation_equal_count,
        "avg_abs_generated_char_delta": _avg_abs(item.get("generated_char_delta") for item in comparisons),
        "avg_abs_continuation_char_delta": _avg_abs(item.get("continuation_char_delta") for item in comparisons),
        "task_type_counts": task_type_counts,
        "difficulty_counts": difficulty_counts,
        "task_type_summary": _summary_by(results, "task_type"),
        "difficulty_summary": _summary_by(results, "difficulty"),
        "results": results,
    }


def write_pair_batch_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_pair_batch_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "task_type",
        "difficulty",
        "seed",
        "max_new_tokens",
        "temperature",
        "top_k",
        "left_checkpoint_id",
        "right_checkpoint_id",
        "generated_equal",
        "continuation_equal",
        "generated_char_delta",
        "continuation_char_delta",
        "left_continuation_chars",
        "right_continuation_chars",
        "prompt",
        "left_continuation",
        "right_continuation",
        "expected_behavior",
        "tags",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in report.get("results", []):
            comparison = _pick_dict(result, "comparison")
            left = _pick_dict(result, "left")
            right = _pick_dict(result, "right")
            writer.writerow(
                {
                    "name": result.get("name"),
                    "task_type": result.get("task_type"),
                    "difficulty": result.get("difficulty"),
                    "seed": result.get("seed"),
                    "max_new_tokens": result.get("max_new_tokens"),
                    "temperature": result.get("temperature"),
                    "top_k": result.get("top_k"),
                    "left_checkpoint_id": left.get("checkpoint_id"),
                    "right_checkpoint_id": right.get("checkpoint_id"),
                    "generated_equal": comparison.get("generated_equal"),
                    "continuation_equal": comparison.get("continuation_equal"),
                    "generated_char_delta": comparison.get("generated_char_delta"),
                    "continuation_char_delta": comparison.get("continuation_char_delta"),
                    "left_continuation_chars": comparison.get("left_continuation_chars"),
                    "right_continuation_chars": comparison.get("right_continuation_chars"),
                    "prompt": result.get("prompt"),
                    "left_continuation": left.get("continuation"),
                    "right_continuation": right.get("continuation"),
                    "expected_behavior": result.get("expected_behavior"),
                    "tags": ",".join(result.get("tags") or []),
                }
            )


def render_pair_batch_markdown(report: dict[str, Any]) -> str:
    suite = _pick_dict(report, "suite")
    left = _pick_dict(report, "left")
    right = _pick_dict(report, "right")
    lines = [
        "# MiniGPT Pair Generation Batch",
        "",
        f"- Suite: {suite.get('name') or 'n/a'} v{suite.get('version') or 'n/a'}",
        f"- Left: {left.get('checkpoint_id')} ({left.get('checkpoint')})",
        f"- Right: {right.get('checkpoint_id')} ({right.get('checkpoint')})",
        f"- Cases: {report.get('case_count')}",
        f"- Generated equal: {report.get('generated_equal_count')}",
        f"- Continuation equal: {report.get('continuation_equal_count')}",
        f"- Avg abs generated delta: {report.get('avg_abs_generated_char_delta')}",
        f"- Avg abs continuation delta: {report.get('avg_abs_continuation_char_delta')}",
        "",
        "| Case | Task | Generated Equal | Char Delta | Left Continuation | Right Continuation |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for result in report.get("results", []):
        comparison = _pick_dict(result, "comparison")
        left_result = _pick_dict(result, "left")
        right_result = _pick_dict(result, "right")
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(result.get("name")),
                    _md(result.get("task_type")),
                    _md(comparison.get("generated_equal")),
                    _md(comparison.get("generated_char_delta")),
                    _md(_clip(str(left_result.get("continuation") or ""), 70)),
                    _md(_clip(str(right_result.get("continuation") or ""), 70)),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_pair_batch_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_pair_batch_markdown(report), encoding="utf-8")


def render_pair_batch_html(report: dict[str, Any]) -> str:
    suite = _pick_dict(report, "suite")
    left = _pick_dict(report, "left")
    right = _pick_dict(report, "right")
    stats = [
        ("Suite", f"{suite.get('name') or 'n/a'} v{suite.get('version') or 'n/a'}"),
        ("Cases", report.get("case_count")),
        ("Generated equal", report.get("generated_equal_count")),
        ("Continuation equal", report.get("continuation_equal_count")),
        ("Avg gen delta", report.get("avg_abs_generated_char_delta")),
        ("Avg cont delta", report.get("avg_abs_continuation_char_delta")),
        ("Left", left.get("checkpoint_id")),
        ("Right", right.get("checkpoint_id")),
    ]
    rows = []
    for result in report.get("results", []):
        comparison = _pick_dict(result, "comparison")
        left_result = _pick_dict(result, "left")
        right_result = _pick_dict(result, "right")
        rows.append(
            "<tr>"
            f"<td>{_e(result.get('name'))}</td>"
            f"<td>{_e(result.get('task_type'))}</td>"
            f"<td>{_e(result.get('difficulty'))}</td>"
            f"<td>{_e(result.get('seed'))}</td>"
            f"<td>{_e(comparison.get('generated_equal'))}</td>"
            f"<td>{_e(comparison.get('generated_char_delta'))}</td>"
            f"<td>{_e(_clip(str(left_result.get('continuation') or ''), 80))}</td>"
            f"<td>{_e(_clip(str(right_result.get('continuation') or ''), 80))}</td>"
            "</tr>"
        )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>MiniGPT pair generation batch</title>",
            _html_style(),
            "</head>",
            "<body>",
            "<header>",
            "<h1>MiniGPT Pair Generation Batch</h1>",
            f"<p>{_e(suite.get('description') or 'Fixed prompt pair-generation comparison')}</p>",
            "</header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Checkpoint Pair</h2>'
            f"<p><strong>Left:</strong> {_e(left.get('checkpoint'))}</p>"
            f"<p><strong>Right:</strong> {_e(right.get('checkpoint'))}</p>"
            "</section>",
            '<section class="panel"><h2>Prompt Pair Results</h2><table><thead><tr><th>Case</th><th>Task</th><th>Difficulty</th><th>Seed</th><th>Equal</th><th>Delta</th><th>Left Continuation</th><th>Right Continuation</th></tr></thead><tbody>'
            + "".join(rows)
            + "</tbody></table></section>",
            "<footer>Generated by MiniGPT pair batch.</footer>",
            "</body></html>",
        ]
    )


def write_pair_batch_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_pair_batch_html(report), encoding="utf-8")


def write_pair_batch_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "pair_generation_batch.json",
        "csv": root / "pair_generation_batch.csv",
        "md": root / "pair_generation_batch.md",
        "html": root / "pair_generation_batch.html",
    }
    write_pair_batch_json(report, paths["json"])
    write_pair_batch_csv(report, paths["csv"])
    write_pair_batch_markdown(report, paths["md"])
    write_pair_batch_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _response_payload(response: Any, checkpoint_id: str) -> dict[str, Any]:
    if hasattr(response, "to_dict"):
        payload = response.to_dict()
    elif is_dataclass(response):
        payload = asdict(response)
    elif isinstance(response, dict):
        payload = dict(response)
    else:
        raise TypeError("response must be a dict, dataclass, or object with to_dict")
    payload["checkpoint_id"] = payload.get("checkpoint_id") or checkpoint_id
    payload["generated"] = str(payload.get("generated") or "")
    payload["continuation"] = str(payload.get("continuation") or "")
    return payload


def _summary_by(results: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        buckets.setdefault(str(result.get(key) or "unknown"), []).append(result)
    summaries = []
    for name in sorted(buckets):
        items = buckets[name]
        comparisons = [_pick_dict(item, "comparison") for item in items]
        summaries.append(
            {
                "key": name,
                "case_count": len(items),
                "generated_equal_count": sum(1 for item in comparisons if item.get("generated_equal") is True),
                "avg_abs_generated_char_delta": _avg_abs(item.get("generated_char_delta") for item in comparisons),
                "avg_abs_continuation_char_delta": _avg_abs(item.get("continuation_char_delta") for item in comparisons),
            }
        )
    return summaries


def _count_by(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _avg_abs(values: Any) -> float:
    items = [abs(int(value)) for value in values if value is not None]
    if not items:
        return 0.0
    return round(sum(items) / len(items), 4)


def _pick_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _clip(text: str, limit: int) -> str:
    flat = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "..."


def _md(value: Any) -> str:
    return str("" if value is None else value).replace("|", "\\|").replace("\n", "\\n")


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
p { margin:0 0 8px; color:var(--muted); overflow-wrap:anywhere; }
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
