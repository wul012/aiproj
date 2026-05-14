from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_json_payload,
)
from minigpt.training_scale_run_comparison import build_training_scale_run_comparison


def load_training_scale_promotion_index(path: str | Path) -> dict[str, Any]:
    index_path = _resolve_index_path(Path(path))
    payload = json.loads(index_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale promotion index must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(index_path)
    return payload


def build_promoted_training_scale_comparison(
    promotion_index_path: str | Path,
    *,
    baseline: str | int | None = None,
    generated_at: str | None = None,
    title: str = "MiniGPT promoted training scale comparison",
) -> dict[str, Any]:
    index = load_training_scale_promotion_index(promotion_index_path)
    index_file = Path(str(index.get("_source_path")))
    index_dir = index_file.parent
    index_summary = _dict(index.get("summary"))
    index_comparison = _dict(index.get("comparison_inputs"))
    promotions = _promotion_rows(index, index_dir)
    compare_rows = [row for row in promotions if row.get("promoted_for_comparison")]
    comparison_inputs = _comparison_inputs(index_comparison, compare_rows, index_dir)
    blocked_reason = None
    comparison_report: dict[str, Any] = {}
    comparison_status = "blocked"
    if len(comparison_inputs["resolved_paths"]) < 2:
        blocked_reason = "at least two promoted runs are required to compare"
    elif comparison_inputs["missing_paths"]:
        blocked_reason = "missing promoted run paths: " + ", ".join(comparison_inputs["missing_paths"])
    else:
        try:
            comparison_report = build_training_scale_run_comparison(
                comparison_inputs["resolved_paths"],
                names=comparison_inputs["names"],
                baseline=baseline if baseline is not None else comparison_inputs["baseline_name"],
                title=title,
                generated_at=generated_at,
            )
            comparison_status = "compared"
        except Exception as exc:  # pragma: no cover - converted into report data
            blocked_reason = str(exc)
    promotions = _merge_comparison_rows(promotions, comparison_report)
    summary = _summary(index_summary, promotions, comparison_inputs, comparison_report, comparison_status, blocked_reason)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "promotion_index_path": str(index_file),
        "promotion_index_summary": index_summary,
        "promotions": promotions,
        "comparison_inputs": comparison_inputs,
        "comparison_status": comparison_status,
        "comparison": comparison_report,
        "summary": summary,
        "blockers": _blockers(blocked_reason, comparison_inputs, comparison_status),
        "recommendations": _recommendations(summary),
    }


def write_promoted_training_scale_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_promoted_training_scale_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    comparison = _dict(report.get("comparison"))
    deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "promotion_status",
        "promoted_for_comparison",
        "training_scale_run_path",
        "status",
        "allowed",
        "gate_status",
        "batch_status",
        "readiness_score",
        "baseline_name",
        "is_baseline",
        "readiness_delta",
        "gate_relation",
        "batch_relation",
        "explanation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("promotions")):
            delta = deltas.get(row.get("name"), {})
            writer.writerow(
                {
                    "name": row.get("name"),
                    "promotion_status": row.get("promotion_status"),
                    "promoted_for_comparison": row.get("promoted_for_comparison"),
                    "training_scale_run_path": row.get("training_scale_run_path"),
                    "status": row.get("comparison_status"),
                    "allowed": row.get("allowed"),
                    "gate_status": row.get("gate_status"),
                    "batch_status": row.get("batch_status"),
                    "readiness_score": row.get("readiness_score"),
                    "baseline_name": delta.get("baseline_name"),
                    "is_baseline": delta.get("is_baseline"),
                    "readiness_delta": delta.get("readiness_delta"),
                    "gate_relation": delta.get("gate_relation"),
                    "batch_relation": delta.get("batch_relation"),
                    "explanation": delta.get("explanation"),
                }
            )


def render_promoted_training_scale_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    comparison = _dict(report.get("comparison"))
    lines = [
        f"# {report.get('title', 'MiniGPT promoted training scale comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Comparison status: `{report.get('comparison_status')}`",
        f"- Promoted inputs: `{summary.get('promoted_count')}`",
        f"- Compare-ready inputs: `{summary.get('comparison_ready_count')}`",
        f"- Compared runs: `{summary.get('compared_run_count')}`",
        f"- Baseline: `{summary.get('baseline_name')}`",
        "",
        "## Promoted Inputs",
        "",
        "| Name | Status | Compare | Readiness | Run |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in _list_of_dicts(report.get("promotions")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(row.get("promotion_status")),
                    _md(row.get("promoted_for_comparison")),
                    _md(row.get("readiness_score")),
                    _md(row.get("training_scale_run_path")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Comparison", ""])
    if report.get("comparison_status") == "compared":
        lines.extend(
            [
                f"- Compared runs: `{comparison.get('run_count')}`",
                f"- Allowed: `{comparison.get('summary', {}).get('allowed_count')}`",
                f"- Blocked: `{comparison.get('summary', {}).get('blocked_count')}`",
                f"- Best by readiness: `{_dict(comparison.get('best_by_readiness')).get('name')}`",
            ]
        )
        lines.extend(["", "| Run | Status | Allowed | Gate | Batch | Score | Relation |", "| --- | --- | --- | --- | --- | ---: | --- |"])
        deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
        for row in _list_of_dicts(comparison.get("runs")):
            delta = deltas.get(row.get("name"), {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md(row.get("name")),
                        _md(row.get("status")),
                        _md(row.get("allowed")),
                        _md(row.get("gate_status")),
                        _md(row.get("batch_status")),
                        _md(row.get("readiness_score")),
                        _md(delta.get("explanation")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("- " + (_block_reason(report) or "Comparison is blocked."))
    blockers = _string_list(report.get("blockers"))
    if blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in blockers)
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_promoted_training_scale_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_comparison_markdown(report), encoding="utf-8")


def render_promoted_training_scale_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    comparison = _dict(report.get("comparison"))
    stats = [
        ("Status", report.get("comparison_status")),
        ("Promoted", summary.get("promoted_count")),
        ("Compare-ready", summary.get("comparison_ready_count")),
        ("Compared", summary.get("compared_run_count")),
        ("Baseline", summary.get("baseline_name")),
        ("Best", _dict(comparison.get("best_by_readiness")).get("name")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT promoted training scale comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT promoted training scale comparison'))}</h1><p>{_e(report.get('promotion_index_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _promotion_table(report),
            _comparison_table(report),
            _list_section("Blockers", report.get("blockers")),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT promoted training scale comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_promoted_training_scale_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_promoted_training_scale_comparison_html(report), encoding="utf-8")


def write_promoted_training_scale_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "promoted_training_scale_comparison.json",
        "csv": root / "promoted_training_scale_comparison.csv",
        "markdown": root / "promoted_training_scale_comparison.md",
        "html": root / "promoted_training_scale_comparison.html",
    }
    write_promoted_training_scale_comparison_json(report, paths["json"])
    write_promoted_training_scale_comparison_csv(report, paths["csv"])
    write_promoted_training_scale_comparison_markdown(report, paths["markdown"])
    write_promoted_training_scale_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_index_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "training_scale_promotion_index.json",
                path / "promotion-index" / "training_scale_promotion_index.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _promotion_rows(index: dict[str, Any], index_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for row in _list_of_dicts(index.get("promotions")):
        run_path = row.get("training_scale_run_path")
        resolved_run_path = _resolve_path(run_path, index_dir)
        rows.append(
            {
                "name": row.get("name"),
                "promotion_status": row.get("promotion_status"),
                "promoted_for_comparison": bool(row.get("promoted_for_comparison")),
                "training_scale_run_path": str(resolved_run_path),
                "training_scale_run_exists": resolved_run_path.exists(),
                "gate_status": row.get("gate_status"),
                "batch_status": row.get("batch_status"),
                "readiness_score": row.get("readiness_score"),
            }
        )
    return rows


def _comparison_inputs(
    index_comparison: dict[str, Any],
    compare_rows: list[dict[str, Any]],
    index_dir: Path,
) -> dict[str, Any]:
    names = [str(row.get("name")) for row in compare_rows if row.get("name")]
    paths = [str(row.get("training_scale_run_path")) for row in compare_rows if row.get("training_scale_run_path")]
    resolved_paths = [_resolve_path(path, index_dir) for path in paths]
    missing_paths = [str(path) for path in resolved_paths if not path.exists()]
    baseline_name = index_comparison.get("baseline_name")
    if baseline_name and baseline_name not in names and names:
        baseline_name = names[0]
    return {
        "run_count": len(compare_rows),
        "names": names,
        "training_scale_run_paths": paths,
        "resolved_paths": [str(path) for path in resolved_paths],
        "missing_paths": missing_paths,
        "baseline_name": baseline_name,
        "compare_command_ready": len(compare_rows) >= 2 and not missing_paths,
    }


def _merge_comparison_rows(promotions: list[dict[str, Any]], comparison_report: dict[str, Any]) -> list[dict[str, Any]]:
    runs = {row.get("name"): row for row in _list_of_dicts(comparison_report.get("runs"))}
    merged = []
    for row in promotions:
        updated = dict(row)
        run = runs.get(row.get("name"))
        if run:
            updated.update(
                {
                    "comparison_status": run.get("status"),
                    "allowed": run.get("allowed"),
                    "gate_status": run.get("gate_status"),
                    "batch_status": run.get("batch_status"),
                    "readiness_score": run.get("readiness_score"),
                }
            )
        merged.append(updated)
    return merged


def _summary(
    index_summary: dict[str, Any],
    promotions: list[dict[str, Any]],
    comparison_inputs: dict[str, Any],
    comparison_report: dict[str, Any],
    comparison_status: str,
    blocked_reason: str | None,
) -> dict[str, Any]:
    compared = _dict(comparison_report.get("summary"))
    return {
        "comparison_status": comparison_status,
        "promotion_index_status": _index_status(index_summary),
        "promotion_count": len(promotions),
        "promoted_count": sum(1 for row in promotions if row.get("promotion_status") == "promoted"),
        "comparison_ready_count": comparison_inputs.get("run_count"),
        "compared_run_count": _dict(comparison_report.get("summary")).get("run_count"),
        "baseline_name": compared.get("baseline_name") or comparison_inputs.get("baseline_name"),
        "best_by_readiness": _dict(comparison_report.get("best_by_readiness")).get("name"),
        "allowed_count": compared.get("allowed_count"),
        "blocked_count": compared.get("blocked_count"),
        "gate_warn_count": compared.get("gate_warn_count"),
        "gate_fail_count": compared.get("gate_fail_count"),
        "blocked_reason": blocked_reason,
    }


def _blockers(blocked_reason: str | None, comparison_inputs: dict[str, Any], comparison_status: str) -> list[str]:
    if comparison_status == "compared":
        return []
    blockers = []
    if blocked_reason:
        blockers.append(blocked_reason)
    if comparison_inputs.get("run_count", 0) < 2:
        blockers.append("need at least two promoted runs for comparison")
    if comparison_inputs.get("missing_paths"):
        blockers.append("missing promoted run paths: " + ", ".join(_string_list(comparison_inputs.get("missing_paths"))))
    return blockers


def _index_status(index_summary: dict[str, Any]) -> str:
    if not index_summary:
        return "unknown"
    if index_summary.get("compare_command_ready"):
        return "compare_ready"
    return "insufficient"


def _recommendations(summary: dict[str, Any]) -> list[str]:
    if summary.get("comparison_status") == "compared":
        return [
            "Use the compared promoted runs as the baseline for the next training-scale decision.",
            "Keep review and blocked promotions in the index, but do not feed them into comparison runs.",
        ]
    return [
        "Add another promoted run or fix the blocked baseline before comparing promoted results.",
        "Use the promotion index to keep review and blocked evidence visible without mixing it into model comparison.",
    ]


def _promotion_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("promotions")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(row.get('promotion_status'))}</td>"
            f"<td>{_e(row.get('promoted_for_comparison'))}</td>"
            f"<td>{_e(row.get('readiness_score'))}</td>"
            f"<td>{_e(row.get('training_scale_run_path'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Promoted Inputs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Name</th><th>Status</th><th>Compare</th><th>Readiness</th><th>Run</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _comparison_table(report: dict[str, Any]) -> str:
    comparison = _dict(report.get("comparison"))
    if report.get("comparison_status") != "compared":
        return f'<section><h2>Comparison</h2><p>{_e(_block_reason(report) or "Comparison is blocked.")}</p></section>'
    deltas = {row.get("name"): row for row in _list_of_dicts(comparison.get("baseline_deltas"))}
    rows = []
    for row in _list_of_dicts(comparison.get("runs")):
        delta = deltas.get(row.get("name"), {})
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(row.get('status'))}</td>"
            f"<td>{_e(row.get('allowed'))}</td>"
            f"<td>{_e(row.get('gate_status'))}</td>"
            f"<td>{_e(row.get('batch_status'))}</td>"
            f"<td>{_e(row.get('readiness_score'))}</td>"
            f"<td>{_e(delta.get('explanation'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Comparison</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Run</th><th>Status</th><th>Allowed</th><th>Gate</th><th>Batch</th><th>Score</th><th>Relation</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f8f4; color: #162126; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1180px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d6ddd6; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #52635a; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9e1da; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(22, 33, 38, 0.05); }
.card span { display: block; color: #64756c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 860px; }
th, td { text-align: left; border-bottom: 1px solid #e4e9e4; padding: 9px; vertical-align: top; }
th { color: #435249; font-size: 12px; text-transform: uppercase; }
li { margin: 7px 0; }
footer { color: #69786e; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _resolve_path(value: Any, base_dir: Path) -> Path:
    if value is None:
        return base_dir
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidates = [base_dir / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _block_reason(report: dict[str, Any]) -> str | None:
    return _dict(report.get("summary")).get("blocked_reason") or (_string_list(report.get("blockers"))[0] if _string_list(report.get("blockers")) else None)
