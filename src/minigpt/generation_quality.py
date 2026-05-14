from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)


def build_generation_quality_report(
    source_path: str | Path,
    *,
    source_type: str = "auto",
    min_continuation_chars: int = 8,
    min_unique_ratio: float = 0.25,
    max_repeat_run: int = 8,
    max_repeated_ngram_ratio: float = 0.65,
    ngram_size: int = 2,
    title: str = "MiniGPT generation quality report",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if min_continuation_chars < 1:
        raise ValueError("min_continuation_chars must be at least 1")
    if not 0 < min_unique_ratio <= 1:
        raise ValueError("min_unique_ratio must be in (0, 1]")
    if max_repeat_run < 1:
        raise ValueError("max_repeat_run must be at least 1")
    if not 0 <= max_repeated_ngram_ratio <= 1:
        raise ValueError("max_repeated_ngram_ratio must be in [0, 1]")
    if ngram_size < 1:
        raise ValueError("ngram_size must be at least 1")

    source_file = Path(source_path)
    payload = _read_required_json(source_file)
    inferred_type = _infer_source_type(payload) if source_type == "auto" else source_type
    cases = _build_case_rows(
        payload,
        inferred_type,
        min_continuation_chars=min_continuation_chars,
        min_unique_ratio=min_unique_ratio,
        max_repeat_run=max_repeat_run,
        max_repeated_ngram_ratio=max_repeated_ngram_ratio,
        ngram_size=ngram_size,
    )
    summary = _build_summary(cases, inferred_type)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "source_path": str(source_file),
        "source_type": inferred_type,
        "policy": {
            "min_continuation_chars": min_continuation_chars,
            "min_unique_ratio": min_unique_ratio,
            "max_repeat_run": max_repeat_run,
            "max_repeated_ngram_ratio": max_repeated_ngram_ratio,
            "ngram_size": ngram_size,
        },
        "summary": summary,
        "cases": cases,
        "recommendations": _recommendations(summary, cases),
        "warnings": _warnings(payload, cases),
    }


def write_generation_quality_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_generation_quality_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "status",
        "char_count",
        "unique_char_count",
        "unique_ratio",
        "repeated_ngram_ratio",
        "longest_repeat_run",
        "flag_count",
        "flags",
        "prompt",
        "continuation_preview",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in _list_of_dicts(report.get("cases")):
            row = {field: case.get(field) for field in fieldnames}
            row["flags"] = ";".join(_flag_ids(case))
            writer.writerow(row)


def render_generation_quality_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    policy = _dict(report.get("policy"))
    lines = [
        f"# {report.get('title', 'MiniGPT generation quality report')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Source: `{report.get('source_path')}`",
        f"- Source type: `{report.get('source_type')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Overall status", summary.get("overall_status")),
                ("Cases", summary.get("case_count")),
                ("Pass", summary.get("pass_count")),
                ("Warn", summary.get("warn_count")),
                ("Fail", summary.get("fail_count")),
                ("Avg chars", summary.get("avg_continuation_chars")),
                ("Avg unique ratio", summary.get("avg_unique_ratio")),
                ("Avg repeated ngram ratio", summary.get("avg_repeated_ngram_ratio")),
                ("Max repeat run", summary.get("max_repeat_run")),
            ]
        ),
        "",
        "## Policy",
        "",
        *_markdown_table([(key, value) for key, value in policy.items()]),
        "",
        "## Cases",
        "",
        "| Status | Case | Chars | Unique Ratio | Repeated Ngram | Repeat Run | Flags |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in _list_of_dicts(report.get("cases")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(case.get("status")),
                    _md(case.get("name")),
                    _md(case.get("char_count")),
                    _md(_ratio_label(case.get("unique_ratio"))),
                    _md(_ratio_label(case.get("repeated_ngram_ratio"))),
                    _md(case.get("longest_repeat_run")),
                    _md(", ".join(_flag_ids(case)) or "none"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    warnings = _string_list(report.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_generation_quality_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_generation_quality_markdown(report), encoding="utf-8")


def write_generation_quality_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cases = _list_of_dicts(report.get("cases"))
    width = 1040
    row_h = 70
    top = 98
    height = top + row_h * len(cases) + 58
    bar_x = 290
    bar_w = 420
    rows: list[str] = []
    for index, case in enumerate(cases):
        y = top + index * row_h
        ratio = _number(case.get("unique_ratio")) or 0.0
        repeated = _number(case.get("repeated_ngram_ratio")) or 0.0
        unique_bar = max(2, int(bar_w * min(1.0, ratio)))
        repeated_bar = max(2, int(bar_w * min(1.0, repeated)))
        color = _status_color(str(case.get("status") or "warn"))
        label = f"{case.get('name')}  {case.get('status')}  flags={case.get('flag_count')}"
        rows.append(f'<text x="28" y="{y + 16}" font-family="Arial" font-size="13" fill="#111827">{_e(label)}</text>')
        rows.append(f'<rect x="{bar_x}" y="{y + 24}" width="{unique_bar}" height="12" rx="3" fill="{color}"/>')
        rows.append(f'<rect x="{bar_x}" y="{y + 42}" width="{repeated_bar}" height="12" rx="3" fill="#64748b"/>')
        rows.append(f'<text x="{bar_x + bar_w + 16}" y="{y + 35}" font-family="Arial" font-size="12" fill="#374151">unique={_ratio_label(ratio)}</text>')
        rows.append(f'<text x="{bar_x + bar_w + 16}" y="{y + 53}" font-family="Arial" font-size="12" fill="#374151">repeat={_ratio_label(repeated)}</text>')
        rows.append(f'<text x="28" y="{y + 48}" font-family="Arial" font-size="12" fill="#4b5563">{_e(str(case.get("continuation_preview") or ""))}</text>')
    summary = _dict(report.get("summary"))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">MiniGPT generation quality</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Status: {_e(str(summary.get("overall_status")))} | Cases: {summary.get("case_count")} | Avg chars: {summary.get("avg_continuation_chars")}</text>
  <text x="28" y="78" font-family="Arial" font-size="12" fill="#374151">Colored bars show unique ratio; gray bars show repeated n-gram ratio.</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def render_generation_quality_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Status", summary.get("overall_status")),
        ("Cases", summary.get("case_count")),
        ("Pass", summary.get("pass_count")),
        ("Warn", summary.get("warn_count")),
        ("Fail", summary.get("fail_count")),
        ("Avg chars", summary.get("avg_continuation_chars")),
        ("Avg unique", _ratio_label(summary.get("avg_unique_ratio"))),
        ("Max repeat", summary.get("max_repeat_run")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT generation quality report'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT generation quality report'))}</h1><p>{_e(report.get('source_path'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _key_value_section("Policy", _dict(report.get("policy"))),
            _case_section(_list_of_dicts(report.get("cases"))),
            _list_section("Recommendations", report.get("recommendations")),
            _list_section("Warnings", report.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT generation quality analyzer.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_generation_quality_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_generation_quality_html(report), encoding="utf-8")


def write_generation_quality_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "generation_quality.json",
        "csv": root / "generation_quality.csv",
        "markdown": root / "generation_quality.md",
        "svg": root / "generation_quality.svg",
        "html": root / "generation_quality.html",
    }
    write_generation_quality_json(report, paths["json"])
    write_generation_quality_csv(report, paths["csv"])
    write_generation_quality_markdown(report, paths["markdown"])
    write_generation_quality_svg(report, paths["svg"])
    write_generation_quality_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"generation quality input must be a JSON object: {path}")
    return payload


def _infer_source_type(payload: dict[str, Any]) -> str:
    if "case_count" in payload and "avg_continuation_chars" in payload:
        return "eval_suite"
    if "max_new_tokens" in payload and "prompt" in payload:
        return "sample_lab"
    return "generic_results"


def _build_case_rows(
    payload: dict[str, Any],
    source_type: str,
    *,
    min_continuation_chars: int,
    min_unique_ratio: float,
    max_repeat_run: int,
    max_repeated_ngram_ratio: float,
    ngram_size: int,
) -> list[dict[str, Any]]:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list) or not raw_results:
        raise ValueError("generation quality input requires a non-empty results list")
    rows = []
    shared_prompt = str(payload.get("prompt") or "")
    for index, item in enumerate(raw_results, start=1):
        if not isinstance(item, dict):
            raise ValueError("each generation result must be an object")
        prompt = str(item.get("prompt") or shared_prompt)
        continuation = _continuation(item, prompt)
        metrics = _metrics(continuation, ngram_size=ngram_size)
        flags = _flags(
            continuation,
            prompt,
            metrics,
            min_continuation_chars=min_continuation_chars,
            min_unique_ratio=min_unique_ratio,
            max_repeat_run=max_repeat_run,
            max_repeated_ngram_ratio=max_repeated_ngram_ratio,
        )
        status = _status(flags)
        rows.append(
            {
                "name": str(item.get("name") or f"case-{index}"),
                "source_type": source_type,
                "status": status,
                "prompt": prompt,
                "temperature": item.get("temperature"),
                "top_k": item.get("top_k"),
                "seed": item.get("seed"),
                "max_new_tokens": item.get("max_new_tokens") or payload.get("max_new_tokens"),
                "char_count": metrics["char_count"],
                "stripped_char_count": metrics["stripped_char_count"],
                "unique_char_count": metrics["unique_char_count"],
                "unique_ratio": metrics["unique_ratio"],
                "repeated_ngram_ratio": metrics["repeated_ngram_ratio"],
                "longest_repeat_run": metrics["longest_repeat_run"],
                "flag_count": len(flags),
                "flags": flags,
                "continuation_preview": _clip(continuation, 96),
            }
        )
    return rows


def _continuation(item: dict[str, Any], prompt: str) -> str:
    continuation = item.get("continuation")
    if isinstance(continuation, str):
        return continuation
    generated = item.get("generated")
    if not isinstance(generated, str):
        return ""
    if prompt and generated.startswith(prompt):
        return generated[len(prompt) :]
    return generated


def _metrics(text: str, *, ngram_size: int) -> dict[str, Any]:
    non_ws = [char for char in text if not char.isspace()]
    ngrams = _ngrams(non_ws, ngram_size)
    unique_ratio = 0.0 if not non_ws else len(set(non_ws)) / len(non_ws)
    repeated_ngram_ratio = 0.0 if not ngrams else 1.0 - len(set(ngrams)) / len(ngrams)
    return {
        "char_count": len(text),
        "stripped_char_count": len(text.strip()),
        "unique_char_count": len(set(non_ws)),
        "unique_ratio": round(unique_ratio, 4),
        "repeated_ngram_ratio": round(repeated_ngram_ratio, 4),
        "longest_repeat_run": _longest_repeat_run(non_ws),
    }


def _ngrams(chars: list[str], size: int) -> list[str]:
    if len(chars) < size:
        return []
    return ["".join(chars[index : index + size]) for index in range(len(chars) - size + 1)]


def _longest_repeat_run(chars: list[str]) -> int:
    if not chars:
        return 0
    longest = 1
    current = 1
    previous = chars[0]
    for char in chars[1:]:
        if char == previous:
            current += 1
        else:
            longest = max(longest, current)
            current = 1
            previous = char
    return max(longest, current)


def _flags(
    continuation: str,
    prompt: str,
    metrics: dict[str, Any],
    *,
    min_continuation_chars: int,
    min_unique_ratio: float,
    max_repeat_run: int,
    max_repeated_ngram_ratio: float,
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    if metrics["stripped_char_count"] == 0:
        flags.append(_flag("empty_continuation", "fail", "Continuation is empty."))
    elif metrics["char_count"] < min_continuation_chars:
        flags.append(_flag("too_short", "fail", f"Continuation has {metrics['char_count']} chars; minimum is {min_continuation_chars}."))
    if metrics["char_count"] and metrics["unique_ratio"] < min_unique_ratio:
        flags.append(_flag("low_diversity", "warn", f"Unique ratio {_ratio_label(metrics['unique_ratio'])} is below {_ratio_label(min_unique_ratio)}."))
    if metrics["longest_repeat_run"] > max_repeat_run:
        flags.append(_flag("long_repeat_run", "warn", f"Longest repeated character run is {metrics['longest_repeat_run']}; maximum is {max_repeat_run}."))
    if metrics["repeated_ngram_ratio"] > max_repeated_ngram_ratio:
        flags.append(_flag("high_ngram_repetition", "warn", f"Repeated n-gram ratio {_ratio_label(metrics['repeated_ngram_ratio'])} is above {_ratio_label(max_repeated_ngram_ratio)}."))
    if _looks_like_prompt_echo(continuation, prompt):
        flags.append(_flag("prompt_echo", "warn", "Continuation appears to repeat the prompt."))
    return flags


def _looks_like_prompt_echo(continuation: str, prompt: str) -> bool:
    cleaned_prompt = prompt.strip()
    if len(cleaned_prompt) < 4:
        return False
    prefix = cleaned_prompt[: min(12, len(cleaned_prompt))]
    return continuation.strip().startswith(prefix)


def _flag(flag_id: str, level: str, detail: str) -> dict[str, str]:
    return {"id": flag_id, "level": level, "detail": detail}


def _status(flags: list[dict[str, str]]) -> str:
    levels = {flag.get("level") for flag in flags}
    if "fail" in levels:
        return "fail"
    if "warn" in levels:
        return "warn"
    return "pass"


def _build_summary(cases: list[dict[str, Any]], source_type: str) -> dict[str, Any]:
    pass_count = sum(1 for case in cases if case.get("status") == "pass")
    warn_count = sum(1 for case in cases if case.get("status") == "warn")
    fail_count = sum(1 for case in cases if case.get("status") == "fail")
    if fail_count:
        overall_status = "fail"
    elif warn_count:
        overall_status = "warn"
    else:
        overall_status = "pass"
    return {
        "overall_status": overall_status,
        "source_type": source_type,
        "case_count": len(cases),
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "avg_continuation_chars": _round_avg(case.get("char_count") for case in cases),
        "avg_unique_ratio": _round_avg(case.get("unique_ratio") for case in cases),
        "avg_repeated_ngram_ratio": _round_avg(case.get("repeated_ngram_ratio") for case in cases),
        "max_repeat_run": max((int(case.get("longest_repeat_run") or 0) for case in cases), default=0),
    }


def _recommendations(summary: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    if summary.get("overall_status") == "pass":
        return ["Generation quality checks passed; keep this report with eval artifacts."]
    items = []
    if summary.get("fail_count"):
        items.append("Fix failed generation cases before using this checkpoint as a release candidate.")
    if summary.get("warn_count"):
        items.append("Review warning cases for repetition, low diversity, or prompt echo before model-card handoff.")
    for case in cases:
        if case.get("status") != "pass":
            flag_ids = ", ".join(flag["id"] for flag in _list_of_dicts(case.get("flags")))
            items.append(f"{case.get('name')}: {flag_ids}")
    return items or ["Review generation samples manually before sharing the run."]


def _warnings(payload: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    warnings = []
    if not payload.get("checkpoint"):
        warnings.append("source report does not include a checkpoint path")
    if not payload.get("tokenizer"):
        warnings.append("source report does not include a tokenizer path")
    if not cases:
        warnings.append("no generation cases were analyzed")
    return warnings


def _case_section(cases: list[dict[str, Any]]) -> str:
    rows = []
    for case in cases:
        status = str(case.get("status") or "warn")
        flags = ", ".join(flag.get("id", "") for flag in _list_of_dicts(case.get("flags"))) or "none"
        rows.append(
            "<tr>"
            f'<td><span class="pill {status}">{_e(status)}</span></td>'
            f"<td><strong>{_e(case.get('name'))}</strong><br><span>{_e(case.get('prompt'))}</span></td>"
            f"<td>{_e(case.get('char_count'))}</td>"
            f"<td>{_e(_ratio_label(case.get('unique_ratio')))}</td>"
            f"<td>{_e(_ratio_label(case.get('repeated_ngram_ratio')))}</td>"
            f"<td>{_e(case.get('longest_repeat_run'))}</td>"
            f"<td>{_e(flags)}<br><span>{_e(case.get('continuation_preview'))}</span></td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Cases</h2><table><thead><tr><th>Status</th><th>Case</th><th>Chars</th><th>Unique</th><th>Repeated Ngram</th><th>Repeat Run</th><th>Flags</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _key_value_section(title: str, payload: dict[str, Any]) -> str:
    rows = "".join(f"<tr><th>{_e(key)}</th><td>{_e(_fmt_any(value))}</td></tr>" for key, value in payload.items())
    return f'<section class="panel"><h2>{_e(title)}</h2><table>{rows}</table></section>'


def _list_section(title: str, values: Any, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt_any(value))}</div>' + "</div>"


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#475569; --line:#d7dee8; --page:#f8fafc; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; --blue:#1d4ed8; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:900px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:54px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {_md(key)} | {_md(value)} |")
    return lines


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _flag_ids(case: dict[str, Any]) -> list[str]:
    return [str(flag.get("id")) for flag in _list_of_dicts(case.get("flags")) if flag.get("id")]


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_avg(values: Any) -> float:
    numbers = [_number(value) for value in values]
    clean = [number for number in numbers if number is not None]
    return 0.0 if not clean else round(sum(clean) / len(clean), 4)


def _ratio_label(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "missing"
    return f"{number:.1%}"


def _status_color(status: str) -> str:
    return {"pass": "#047857", "warn": "#b45309", "fail": "#b91c1c"}.get(status, "#1d4ed8")


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


def _md(value: Any) -> str:
    return _fmt_any(value).replace("|", "\\|").replace("\n", " ")


def _clip(text: str, limit: int) -> str:
    flat = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "..."
