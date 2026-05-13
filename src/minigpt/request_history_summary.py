from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any

from .server import read_request_history_log_records


SUMMARY_CSV_COLUMNS = [
    "request_log",
    "status",
    "total_log_records",
    "invalid_record_count",
    "ok_count",
    "timeout_count",
    "cancelled_count",
    "bad_request_count",
    "error_count",
    "timeout_rate",
    "bad_request_rate",
    "error_rate",
    "stream_request_count",
    "pair_request_count",
    "artifact_request_count",
    "unique_checkpoint_count",
    "latest_timestamp",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_request_history_summary(
    request_log_path: str | Path,
    *,
    title: str = "MiniGPT request history summary",
    generated_at: str | None = None,
) -> dict[str, Any]:
    log_path = Path(request_log_path)
    records, invalid_count = read_request_history_log_records(log_path)
    total = len(records)
    status_counts = _count(records, "status")
    endpoint_counts = _count(records, "endpoint")
    checkpoint_counts = _checkpoint_counts(records)
    stream_records = [record for record in records if record.get("endpoint") == "/api/generate-stream"]
    pair_records = [record for record in records if str(record.get("endpoint", "")).startswith("/api/generate-pair")]
    artifact_records = [record for record in records if record.get("artifact_json") or record.get("artifact_html")]
    latest = max((str(record.get("timestamp")) for record in records if record.get("timestamp")), default=None)
    summary = {
        "status": _summary_status(status_counts, invalid_count, total),
        "request_log_exists": log_path.exists(),
        "total_log_records": total,
        "invalid_record_count": invalid_count,
        "ok_count": status_counts.get("ok", 0),
        "timeout_count": status_counts.get("timeout", 0),
        "cancelled_count": status_counts.get("cancelled", 0),
        "bad_request_count": status_counts.get("bad_request", 0),
        "error_count": status_counts.get("error", 0),
        "timeout_rate": _rate(status_counts.get("timeout", 0), total),
        "bad_request_rate": _rate(status_counts.get("bad_request", 0), total),
        "error_rate": _rate(status_counts.get("error", 0), total),
        "stream_request_count": len(stream_records),
        "pair_request_count": len(pair_records),
        "artifact_request_count": len(artifact_records),
        "unique_checkpoint_count": len(checkpoint_counts),
        "latest_timestamp": latest,
    }
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "request_log": str(log_path),
        "summary": summary,
        "status_counts": status_counts,
        "endpoint_counts": endpoint_counts,
        "checkpoint_counts": checkpoint_counts,
        "recent_requests": records[-10:][::-1],
        "recommendations": _recommendations(summary),
    }


def write_request_history_summary_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_request_history_summary_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    row = {"request_log": report.get("request_log"), **_dict(report.get("summary"))}
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_CSV_COLUMNS)
        writer.writeheader()
        writer.writerow({column: _csv_value(row.get(column)) for column in SUMMARY_CSV_COLUMNS})


def render_request_history_summary_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT request history summary')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Request log: `{report.get('request_log')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Status", summary.get("status")),
                ("Total records", summary.get("total_log_records")),
                ("Invalid records", summary.get("invalid_record_count")),
                ("OK", summary.get("ok_count")),
                ("Timeout", summary.get("timeout_count")),
                ("Bad request", summary.get("bad_request_count")),
                ("Error", summary.get("error_count")),
                ("Timeout rate", summary.get("timeout_rate")),
                ("Bad request rate", summary.get("bad_request_rate")),
                ("Error rate", summary.get("error_rate")),
                ("Stream requests", summary.get("stream_request_count")),
                ("Pair requests", summary.get("pair_request_count")),
                ("Artifact requests", summary.get("artifact_request_count")),
                ("Unique checkpoints", summary.get("unique_checkpoint_count")),
                ("Latest timestamp", summary.get("latest_timestamp")),
            ]
        ),
        "",
        "## Status Counts",
        "",
        *_mapping_table(report.get("status_counts")),
        "",
        "## Endpoint Counts",
        "",
        *_mapping_table(report.get("endpoint_counts")),
        "",
        "## Checkpoint Counts",
        "",
        *_mapping_table(report.get("checkpoint_counts")),
        "",
        "## Recommendations",
        "",
    ]
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_request_history_summary_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_request_history_summary_markdown(report), encoding="utf-8")


def render_request_history_summary_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    stats = [
        ("Status", summary.get("status")),
        ("Records", summary.get("total_log_records")),
        ("Invalid", summary.get("invalid_record_count")),
        ("OK", summary.get("ok_count")),
        ("Timeout", summary.get("timeout_count")),
        ("Bad Req", summary.get("bad_request_count")),
        ("Streams", summary.get("stream_request_count")),
        ("Pairs", summary.get("pair_request_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT request history summary'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT request history summary'))}</h1><p>{_e(report.get('request_log'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _mapping_section("Status Counts", _dict(report.get("status_counts"))),
            _mapping_section("Endpoint Counts", _dict(report.get("endpoint_counts"))),
            _mapping_section("Checkpoint Counts", _dict(report.get("checkpoint_counts"))),
            _recent_section(_list_of_dicts(report.get("recent_requests"))),
            _recommendation_section(_string_list(report.get("recommendations"))),
            "<footer>Generated by MiniGPT request history summary exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_request_history_summary_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_request_history_summary_html(report), encoding="utf-8")


def write_request_history_summary_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "request_history_summary.json",
        "csv": root / "request_history_summary.csv",
        "markdown": root / "request_history_summary.md",
        "html": root / "request_history_summary.html",
    }
    write_request_history_summary_json(report, paths["json"])
    write_request_history_summary_csv(report, paths["csv"])
    write_request_history_summary_markdown(report, paths["markdown"])
    write_request_history_summary_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _summary_status(status_counts: dict[str, int], invalid_count: int, total: int) -> str:
    if total == 0:
        return "empty"
    if status_counts.get("error", 0) or status_counts.get("bad_request", 0):
        return "review"
    if invalid_count:
        return "warn"
    if status_counts.get("timeout", 0) or status_counts.get("cancelled", 0):
        return "watch"
    return "pass"


def _checkpoint_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    fields = [
        "checkpoint_id",
        "requested_checkpoint",
        "left_checkpoint_id",
        "right_checkpoint_id",
        "requested_left_checkpoint",
        "requested_right_checkpoint",
    ]
    for record in records:
        values = {str(record.get(field)) for field in fields if record.get(field) not in {None, ""}}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _recommendations(summary: dict[str, Any]) -> list[str]:
    total = int(summary.get("total_log_records") or 0)
    if total == 0:
        return ["Run local generation before using request history summary as review evidence."]
    recs = []
    if int(summary.get("error_count") or 0) or int(summary.get("bad_request_count") or 0):
        recs.append("Review failed or bad-request rows with /api/request-history-detail before trusting the local inference session.")
    if int(summary.get("timeout_count") or 0):
        recs.append("Inspect timeout rows and consider adjusting max_stream_seconds or max_new_tokens for local demos.")
    if int(summary.get("invalid_record_count") or 0):
        recs.append("Clean or rotate malformed JSONL rows so future summaries do not carry invalid-record warnings.")
    if not recs:
        recs.append("Request history is clean enough to use as local inference smoke evidence.")
    return recs


def _count(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record.get(key)
        if value in {None, ""}:
            continue
        text = str(value)
        counts[text] = counts.get(text, 0) + 1
    return dict(sorted(counts.items()))


def _rate(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def _mapping_table(value: Any) -> list[str]:
    mapping = _dict(value)
    lines = ["| Key | Count |", "| --- | ---: |"]
    if not mapping:
        lines.append("| missing | 0 |")
        return lines
    for key, count in mapping.items():
        lines.append(f"| {_md(key)} | {_md(count)} |")
    return lines


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _mapping_section(title: str, mapping: dict[str, Any]) -> str:
    rows = "".join(f"<tr><td>{_e(key)}</td><td>{_e(value)}</td></tr>" for key, value in mapping.items())
    if not rows:
        rows = "<tr><td>missing</td><td>0</td></tr>"
    return f'<section class="panel"><h2>{_e(title)}</h2><table><tbody>{rows}</tbody></table></section>'


def _recent_section(records: list[dict[str, Any]]) -> str:
    rows = []
    for record in records:
        rows.append(
            "<tr>"
            f"<td>{_e(record.get('log_index'))}</td>"
            f"<td>{_e(record.get('timestamp'))}</td>"
            f"<td>{_e(record.get('endpoint'))}</td>"
            f"<td>{_e(record.get('status'))}</td>"
            f"<td>{_e(_checkpoint_label(record))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Recent Requests</h2><table><thead><tr><th>Log</th><th>Time</th><th>Endpoint</th><th>Status</th><th>Checkpoint</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _checkpoint_label(record: dict[str, Any]) -> Any:
    return (
        record.get("checkpoint_id")
        or record.get("requested_checkpoint")
        or record.get("left_checkpoint_id")
        or record.get("requested_left_checkpoint")
        or "missing"
    )


def _recommendation_section(items: list[str]) -> str:
    return '<section class="panel"><h2>Recommendations</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _style() -> str:
    return """<style>
:root { --ink:#172033; --muted:#536176; --line:#d9e2ec; --panel:#ffffff; --page:#f5f7f4; --blue:#1d4ed8; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.5; }
header { padding:24px 32px 16px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 6px; font-size:27px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; letter-spacing:0; }
p { margin:0; color:var(--muted); overflow-wrap:anywhere; }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(155px, 1fr)); gap:12px; padding:18px 32px 0; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:13px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; }
td, th { padding:8px 6px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:22px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _csv_value(value: Any) -> Any:
    if isinstance(value, float):
        return f"{value:.4f}"
    return value


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
